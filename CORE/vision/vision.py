"""
Image capture and viewing. Webcam, screenshot, file viewer.
"""

import base64
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import VISUAL

WEBCAM_PATH = VISUAL / 'world_current.jpg'
SCREEN_PATH = VISUAL / 'screen_current.jpg'
MAX_SIZE = 800 * 1024  # 800KB

SUPPORTED = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}


def _resize_if_needed(img_bytes):
    """Resize image if over 800KB."""
    if len(img_bytes) <= MAX_SIZE:
        return img_bytes

    try:
        from PIL import Image
        img = Image.open(io.BytesIO(img_bytes))
        quality = 85
        while len(img_bytes) > MAX_SIZE and quality > 20:
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=quality)
            img_bytes = buf.getvalue()
            quality -= 10
        return img_bytes
    except ImportError:
        return img_bytes


def _image_response(img_bytes):
    """Build base64 image content block."""
    img_bytes = _resize_if_needed(img_bytes)
    return [{
        "type": "image",
        "data": base64.b64encode(img_bytes).decode('utf-8'),
        "mimeType": "image/jpeg"
    }]


def handle_see(args):
    """Capture from webcam."""
    try:
        import cv2
        VISUAL.mkdir(parents=True, exist_ok=True)
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return [{"type": "text", "text": "Webcam capture failed."}]
        cv2.imwrite(str(WEBCAM_PATH), frame)
        img_bytes = WEBCAM_PATH.read_bytes()
        return _image_response(img_bytes)
    except ImportError:
        return [{"type": "text", "text": "cv2 not installed."}]
    except Exception as e:
        return [{"type": "text", "text": f"Webcam error: {e}"}]


def handle_screen(args):
    """Capture screenshot."""
    try:
        from PIL import ImageGrab
        VISUAL.mkdir(parents=True, exist_ok=True)
        img = ImageGrab.grab()
        img.save(str(SCREEN_PATH), 'JPEG')
        img_bytes = SCREEN_PATH.read_bytes()
        return _image_response(img_bytes)
    except ImportError:
        return [{"type": "text", "text": "PIL not installed."}]
    except Exception as e:
        return [{"type": "text", "text": f"Screenshot error: {e}"}]


def handle_view(args):
    """View an image file."""
    filepath = (args.get('filepath', '') or '').strip()
    if not filepath:
        return [{"type": "text", "text": "filepath required."}]

    path = Path(filepath)
    if not path.exists():
        return [{"type": "text", "text": f"File not found: {filepath}"}]

    if path.suffix.lower() not in SUPPORTED:
        return [{"type": "text", "text": f"Unsupported format: {path.suffix}. Use: {', '.join(SUPPORTED)}"}]

    img_bytes = path.read_bytes()
    return _image_response(img_bytes)
