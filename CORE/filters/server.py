"""
Filters MCP Server
Deliberation prompts for slow thinking. No database, no state.
"""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from filters import get_filter
from _needs import update_needs


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
        "name": "filter",
        "description": "Deliberation prompt.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "description": "doubt, ethics, stakes, intuition, or more"}
            },
            "required": ["type"]
        }
    }
]


def handle_request(req):
    method = req.get("method", "")
    params = req.get("params", {})
    rid = req.get("id")

    if method == "initialize":
        send_response(rid, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "filters", "version": "1.0.0"}
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

        if name == "filter":
            filter_type = args.get("type", "")
            result = get_filter(filter_type)
            send_response(rid, {"content": [{"type": "text", "text": result}]})
            update_needs("filters", "filter")
        else:
            send_error(rid, -32601, f"Unknown tool: {name}")
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
