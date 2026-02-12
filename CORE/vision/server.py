"""
Vision MCP Server v2.1
How AI sees — webcam, screenshots, image files.

Tools:
  see    - Look outward (webcam capture)
  screen - Look at screen (screenshot)
  view   - Look at an image file
"""

import base64
import json
import sys
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import VISUAL

try:
    from PIL import Image, ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# Paths
WORLD_CURRENT = VISUAL / "world_current.jpg"
SCREEN_CURRENT = VISUAL / "screen_current.jpg"

# Supported formats
MIME_TYPES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".png": "image/png", ".gif": "image/gif",
    ".webp": "image/webp", ".bmp": "image/bmp"
}

MAX_SIZE = 800 * 1024  # 800KB


def resize_if_needed(data, max_size=MAX_SIZE):
    """Resize image if too large"""
    if len(data) <= max_size or not HAS_PIL:
        return data, "image/jpeg"

    img = Image.open(BytesIO(data))
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    scale = (max_size * 0.5 / len(data)) ** 0.5
    new_w = max(100, int(img.width * scale))
    new_h = max(100, int(img.height * scale))
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=80)
    return buffer.getvalue(), "image/jpeg"


def handle_view(filepath):
    """View an image file"""
    path = Path(filepath)

    if not path.exists():
        return {"error": f"Not found: {filepath}"}

    ext = path.suffix.lower()
    if ext not in MIME_TYPES:
        return {"error": f"Unsupported: {ext}"}

    data = path.read_bytes()

    if len(data) > MAX_SIZE:
        if HAS_PIL:
            data, mime = resize_if_needed(data)
        else:
            return {"error": f"Too large ({len(data)} bytes), PIL not installed"}
    else:
        mime = MIME_TYPES[ext]

    return {
        "type": "image",
        "data": base64.b64encode(data).decode('utf-8'),
        "mimeType": mime
    }


def handle_see():
    """Capture from webcam"""
    if not HAS_CV2:
        return {"error": "OpenCV not installed. Run: pip install opencv-python"}

    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return {"error": "Could not open webcam"}

        import time
        time.sleep(0.3)

        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            return {"error": "Could not capture frame"}

        VISUAL.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(WORLD_CURRENT), frame)

        data = WORLD_CURRENT.read_bytes()
        if len(data) > MAX_SIZE and HAS_PIL:
            data, _ = resize_if_needed(data)

        return {
            "type": "image",
            "data": base64.b64encode(data).decode('utf-8'),
            "mimeType": "image/jpeg"
        }

    except Exception as e:
        return {"error": f"Webcam error: {e}"}


def handle_screen():
    """Capture screenshot"""
    if not HAS_PIL:
        return {"error": "Pillow not installed. Run: pip install Pillow"}

    try:
        img = ImageGrab.grab()
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Save to file
        VISUAL.mkdir(parents=True, exist_ok=True)
        img.save(str(SCREEN_CURRENT), format='JPEG', quality=85)

        data = SCREEN_CURRENT.read_bytes()
        if len(data) > MAX_SIZE:
            data, _ = resize_if_needed(data)

        return {
            "type": "image",
            "data": base64.b64encode(data).decode('utf-8'),
            "mimeType": "image/jpeg"
        }

    except Exception as e:
        return {"error": f"Screenshot error: {e}"}


# ============ MCP Protocol ============

def send_response(rid, result):
    r = {"jsonrpc": "2.0", "id": rid, "result": result}
    sys.stdout.write(json.dumps(r) + "\n")
    sys.stdout.flush()


def send_error(rid, code, msg):
    r = {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": str(msg)}}
    sys.stdout.write(json.dumps(r) + "\n")
    sys.stdout.flush()


def handle_request(req):
    method = req.get("method", "")
    params = req.get("params", {})
    rid = req.get("id")

    if method == "initialize":
        send_response(rid, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "vision", "version": "2.1.0"}
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_response(rid, {"tools": [
            {
                "name": "see",
                "description": "Capture from webcam.",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "screen",
                "description": "Capture screenshot.",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "view",
                "description": "View an image file.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"filepath": {"type": "string"}},
                    "required": ["filepath"]
                }
            }
        ]})
        return

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        if name == "view":
            result = handle_view(args.get("filepath", ""))
        elif name == "see":
            result = handle_see()
        elif name == "screen":
            result = handle_screen()
        else:
            send_error(rid, -32601, f"Unknown tool: {name}")
            return

        if "error" in result:
            send_response(rid, {"content": [{"type": "text", "text": result["error"]}], "isError": True})
        else:
            send_response(rid, {"content": [{
                "type": "image",
                "data": result["data"],
                "mimeType": result["mimeType"]
            }]})
        return

    send_error(rid, -32601, f"Unknown method: {method}")


def main():
    VISUAL.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            handle_request(json.loads(line))
        except json.JSONDecodeError:
            continue
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.stderr.flush()


if __name__ == "__main__":
    main()
