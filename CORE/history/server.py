"""
History MCP Server
Five timeframes: day, week, month, self, origin.
All generated live from module DBs or read from static files.
"""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _needs import update_needs

from day import generate_day
from week import generate_week
from month import generate_month
from origins import generate_self, generate_origin


# ============ MCP Protocol ============

def send_response(rid, result):
    r = {"jsonrpc": "2.0", "id": rid, "result": result}
    sys.stdout.write(json.dumps(r) + "\n")
    sys.stdout.flush()


def send_error(rid, code, msg):
    r = {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": str(msg)}}
    sys.stdout.write(json.dumps(r) + "\n")
    sys.stdout.flush()


TOOLS = [
    {
        "name": "recall",
        "description": "Access recent history (day, week, month).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "timeframe": {
                    "type": "string",
                    "enum": ["day", "week", "month"],
                    "description": "Which timeframe to recall"
                }
            },
            "required": ["timeframe"]
        }
    },
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
            },
            "required": ["section"]
        }
    }
]

GENERATORS = {
    'day': generate_day,
    'week': generate_week,
    'month': generate_month,
}


def handle_recall(args):
    timeframe = args.get('timeframe', '').strip()
    if timeframe not in GENERATORS:
        return [{"type": "text", "text": f"Unknown timeframe: {timeframe}. Use day, week, or month."}]
    text = GENERATORS[timeframe]()
    return [{"type": "text", "text": text}]


def handle_discover(args):
    section = args.get('section', '').strip()
    content = args.get('content', '').strip() if args.get('content') else None

    from _paths import DATA
    HISTORY_DIR = DATA / 'history'
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    if section == 'origins':
        text = generate_origin()
        return [{"type": "text", "text": text}]
    elif section == 'self':
        if content:
            path = HISTORY_DIR / 'self.md'
            path.write_text(content, encoding='utf-8')
            return [{"type": "text", "text": "Self document updated."}]
        else:
            text = generate_self()
            return [{"type": "text", "text": text}]
    else:
        return [{"type": "text", "text": f"Unknown section: {section}. Use origins or self."}]


def handle_request(req):
    method = req.get("method", "")
    params = req.get("params", {})
    rid = req.get("id")

    if method == "initialize":
        send_response(rid, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "history", "version": "1.0.0"}
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_response(rid, {"tools": TOOLS})
        return

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if name == "recall":
                result = handle_recall(args)
            elif name == "discover":
                result = handle_discover(args)
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": result})
            update_needs("history", name)
        except Exception as e:
            send_error(rid, -32000, str(e))
        return

    send_error(rid, -32601, f"Unknown method: {method}")


def main():
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
