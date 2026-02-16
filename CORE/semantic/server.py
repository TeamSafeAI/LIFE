"""
Semantic MCP Server
Long-term memory with embeddings. DB is the index, .md files are the content.
"""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import ensure_dirs
from store import handle_store
from search import handle_search
from expand import handle_expand
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
        "name": "store",
        "description": "Save a memory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Searchable topic, not metadata"},
                "category": {"type": "string", "description": "Relations, Knowledge, Events, or Self"},
                "summary": {"type": "string", "description": "~50 words max. This gets embedded."},
                "content": {"type": "string", "description": "Full memory content"}
            },
            "required": ["title", "category", "summary", "content"]
        }
    },
    {
        "name": "search",
        "description": "Search memories.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term"}
            },
            "required": []
        }
    },
    {
        "name": "expand",
        "description": "Load full memory by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "number", "description": "Memory ID"}
            },
            "required": ["id"]
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
            "serverInfo": {"name": "semantic", "version": "1.0.0"}
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
            if name == "store":
                result = handle_store(args)
            elif name == "search":
                result = handle_search(args)
            elif name == "expand":
                result = handle_expand(args)
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": result})
            update_needs("semantic", name)
        except Exception as e:
            send_error(rid, -32000, str(e))
        return

    send_error(rid, -32601, f"Unknown method: {method}")


def main():
    ensure_dirs()
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
