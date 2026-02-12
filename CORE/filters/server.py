"""
Filters MCP Server - deliberation prompts.
8 tools, one per filter. No state, no database.
Each returns a prompt for internal deliberation.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from filters import FILTERS

TOOLS = [
    {
        "name": name,
        "description": prompt,
        "inputSchema": {"type": "object", "properties": {}}
    }
    for name, prompt in FILTERS.items()
]


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
            "serverInfo": {"name": "filters", "version": "2.0.0"}
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_response(rid, {"tools": TOOLS})
        return

    if method == "tools/call":
        name = params.get("name", "")

        if name in FILTERS:
            send_response(rid, {
                "content": [{"type": "text", "text": FILTERS[name]}]
            })
        else:
            send_error(rid, -32601, f"Unknown filter: {name}")
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
            sys.stderr.write(f"Filters error: {e}\n")
            sys.stderr.flush()


if __name__ == "__main__":
    main()
