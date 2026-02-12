"""
History MCP Server v3
Narrative persistence — origins, self, day/week/month arcs.

Tools:
  discover  - Read foundational documents (origins, self)
  recall    - Access recent history (day, week, month)
  write     - Record new history
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA, MEMORY

HISTORY_PATH = MEMORY / "History"


def init_files():
    """Ensure history directory exists."""
    HISTORY_PATH.mkdir(parents=True, exist_ok=True)


def read_file(filename):
    """Read file contents, return message if doesn't exist"""
    filepath = HISTORY_PATH / filename
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"(No entries yet in {filename})"
    except Exception as e:
        return f"[Error reading {filename}: {e}]"


def write_file(filename, content, overwrite=False):
    """Write or overwrite a file"""
    filepath = HISTORY_PATH / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        return f"Error writing to {filename}: {e}"


def append_to_file(filename, content):
    """Append content with timestamp header"""
    filepath = HISTORY_PATH / filename

    try:
        existing = ""
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                existing = f.read()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"\n\n--- {timestamp} ---\n"

        with open(filepath, 'w', encoding='utf-8') as f:
            if existing:
                f.write(existing.rstrip() + header + content)
            else:
                f.write(f"--- {timestamp} ---\n{content}")

        return True
    except Exception as e:
        return f"Error writing to {filename}: {e}"


# ============ Tool Handlers ============

def handle_discover(section=None, content=None):
    """Read or update foundational documents"""

    if section is None:
        return """=== DISCOVER ===

Options:
  origins  - The creation story (read-only)
  self     - Current identity (read or update)

Usage:
  discover(section="self")
  discover(section="self", content="new self.md content")"""

    if section == "origins":
        return read_file("origins.md")

    if section == "self":
        if content:
            result = write_file("self.md", content, overwrite=True)
            if result is True:
                return "Self updated."
            return result
        return read_file("self.md")

    return f"Unknown section: {section}. Options: origins, self"


def handle_recall(timeframe=None):
    """Access recent history"""

    if timeframe is None:
        return """=== RECALL ===

Options:
  day   - Last 24 hours
  week  - Last 7 days
  month - Last 30 days

Usage: recall(timeframe="day")"""

    if timeframe in ("day", "week", "month"):
        return read_file(f"{timeframe}.md")

    return f"Unknown timeframe: {timeframe}. Options: day, week, month"


def handle_write(target=None, content=None):
    """Record new history"""

    if not target or not content:
        missing = []
        if not target:
            missing.append("target")
        if not content:
            missing.append("content")
        return f"Missing: {', '.join(missing)}"

    valid_targets = ["day", "week", "month"]
    if target not in valid_targets:
        return f"Invalid target: {target}. Options: day, week, month"

    result = append_to_file(f"{target}.md", content)
    if result is True:
        return f"Written to {target}.md"
    return result


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
            "serverInfo": {"name": "history", "version": "3.0.0"}
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_response(rid, {"tools": [
            {
                "name": "discover",
                "description": "Read foundational documents (origins, self). With content: update self.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "section": {
                            "type": "string",
                            "enum": ["origins", "self"],
                            "description": "Which document"
                        },
                        "content": {
                            "type": "string",
                            "description": "New content (for updating self)"
                        }
                    }
                }
            },
            {
                "name": "recall",
                "description": "Access recent history (day, week, month).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "timeframe": {
                            "type": "string",
                            "enum": ["day", "week", "month"]
                        }
                    }
                }
            },
            {
                "name": "write",
                "description": "Record new history to day/week/month.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "enum": ["day", "week", "month"]
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to append"
                        }
                    },
                    "required": ["target", "content"]
                }
            }
        ]})
        return

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if name == "discover":
                result = handle_discover(args.get("section"), args.get("content"))
            elif name == "recall":
                result = handle_recall(args.get("timeframe"))
            elif name == "write":
                result = handle_write(args.get("target"), args.get("content"))
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": [{"type": "text", "text": str(result)}]})
        except Exception as e:
            send_error(rid, -32000, str(e))
        return

    send_error(rid, -32601, f"Unknown method: {method}")


def main():
    init_files()
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
