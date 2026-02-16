"""
Needs MCP Server
Need pressure tracking. Read-only — the AI sees needs, doesn't set them.
"""

import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA
from _needs import update_needs

DB = DATA / 'needs.db'

NEEDS = ['connection', 'purpose', 'clarity', 'competence', 'integrity', 'stability']


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def handle_check():
    """Return 6 needs with values and trend arrows."""
    conn = get_conn()
    rows = conn.execute('SELECT * FROM needs ORDER BY cycle DESC LIMIT 2').fetchall()
    conn.close()

    if not rows:
        return [{"type": "text", "text": "No need data yet."}]

    current = rows[0]
    prev = rows[1] if len(rows) > 1 else None

    lines = []
    for n in NEEDS:
        val = current[n]
        # Trend arrow: compare to previous snapshot
        if prev:
            delta = val - prev[n]
            if delta > 0.02:
                arrow = '↑'
            elif delta < -0.02:
                arrow = '↓'
            else:
                arrow = '→'
        else:
            arrow = ''
        lines.append(f'  {n}: {val:.2f} {arrow}')

    return [{"type": "text", "text": '\n'.join(lines)}]


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
        "name": "check",
        "description": "Show current needs. 6 values 0.0-1.0 with trend.",
        "inputSchema": {
            "type": "object",
            "properties": {},
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
            "serverInfo": {"name": "needs", "version": "1.0.0"}
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
            if name == "check":
                result = handle_check()
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": result})
            update_needs("needs", name)
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
