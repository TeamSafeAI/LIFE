"""
Working MCP Server
Short-term memory threads with temperature.
"""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from create import handle_create
from add import handle_add
from view import handle_view
from see import handle_see
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
        "name": "create",
        "description": "New thread.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Thread name"},
                "content": {"type": "string", "description": "Summary"}
            },
            "required": ["title", "content"]
        }
    },
    {
        "name": "add",
        "description": "Add note to thread.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "thread": {"type": "string", "description": "Thread title"},
                "title": {"type": "string", "description": "Note title"},
                "content": {"type": "string", "description": "Note body"}
            },
            "required": ["thread", "title", "content"]
        }
    },
    {
        "name": "view",
        "description": "View threads or thread detail.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "thread": {"type": "string", "description": "Thread title"}
            },
            "required": []
        }
    },
    {
        "name": "see",
        "description": "Visual render of a thread.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "thread": {"type": "string", "description": "Thread title"}
            },
            "required": []
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
            "serverInfo": {"name": "working", "version": "1.0.0"}
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
            if name == "create":
                result = handle_create(args)
            elif name == "add":
                result = handle_add(args)
            elif name == "view":
                result = handle_view(args)
            elif name == "see":
                result = handle_see(args)
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": result})
            update_needs("working", name)
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
