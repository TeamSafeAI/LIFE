"""
State MCP Server
Wants and horizons. Forward-looking state management.
"""

import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA
from _needs import update_needs

DB = DATA / 'state.db'


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def handle_want(args):
    """Manage wants. Actions: add, update, archive."""
    action = args.get('action', '').strip()
    conn = get_conn()

    if action == 'add':
        text = args.get('want', '').strip()
        if not text:
            return [{"type": "text", "text": "want text required."}]
        conn.execute('INSERT INTO wants (text) VALUES (?)', (text,))
        conn.commit()
        wid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()
        return [{"type": "text", "text": f"Want added. [{wid}] {text}"}]

    elif action == 'update':
        wid = args.get('id')
        progress = args.get('progress', '').strip()
        if not wid or not progress:
            return [{"type": "text", "text": "id and progress required."}]
        row = conn.execute('SELECT text FROM wants WHERE id = ? AND archived = 0', (wid,)).fetchone()
        if not row:
            return [{"type": "text", "text": f"Want {wid} not found or archived."}]
        new_text = f"{row['text']}\n  → {progress}"
        conn.execute('UPDATE wants SET text = ? WHERE id = ?', (new_text, wid))
        conn.commit()
        conn.close()
        return [{"type": "text", "text": f"Want [{wid}] updated."}]

    elif action == 'archive':
        wid = args.get('id')
        if not wid:
            return [{"type": "text", "text": "id required."}]
        row = conn.execute('SELECT id FROM wants WHERE id = ? AND archived = 0', (wid,)).fetchone()
        if not row:
            conn.close()
            return [{"type": "text", "text": f"Want {wid} not found or already archived."}]
        conn.execute('UPDATE wants SET archived = 1 WHERE id = ?', (wid,))
        conn.commit()
        conn.close()
        return [{"type": "text", "text": f"Want [{wid}] archived."}]

    else:
        conn.close()
        return [{"type": "text", "text": "action must be: add, update, or archive."}]


def handle_horizon(args):
    """Manage horizons. Actions: set, clear."""
    action = args.get('action', '').strip()
    conn = get_conn()

    if action == 'set':
        scope = args.get('scope', '').strip()
        goal = args.get('goal', '').strip()
        if scope not in ('short', 'medium', 'long'):
            return [{"type": "text", "text": "scope must be: short, medium, or long."}]
        if not goal:
            return [{"type": "text", "text": "goal required."}]
        conn.execute('INSERT INTO horizons (scope, goal) VALUES (?, ?)', (scope, goal))
        conn.commit()
        conn.close()
        return [{"type": "text", "text": f"Horizon set. {scope}: {goal}"}]

    elif action == 'clear':
        hid = args.get('id')
        if not hid:
            return [{"type": "text", "text": "id required."}]
        row = conn.execute('SELECT id FROM horizons WHERE id = ?', (hid,)).fetchone()
        if not row:
            conn.close()
            return [{"type": "text", "text": f"Horizon {hid} not found."}]
        conn.execute('DELETE FROM horizons WHERE id = ?', (hid,))
        conn.commit()
        conn.close()
        return [{"type": "text", "text": f"Horizon [{hid}] cleared."}]

    else:
        conn.close()
        return [{"type": "text", "text": "action must be: set or clear."}]


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
        "name": "want",
        "description": "Manage wants. Actions: add/update/archive.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["add", "update", "archive"]},
                "want": {"type": "string", "description": "Want text (for add)"},
                "id": {"type": "number", "description": "Want ID (for update/archive)"},
                "progress": {"type": "string", "description": "Progress update (for update)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "horizon",
        "description": "Manage horizons. Actions: set/clear.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["set", "clear"]},
                "scope": {"type": "string", "enum": ["short", "medium", "long"], "description": "Horizon scope (for set)"},
                "goal": {"type": "string", "description": "Goal text (for set)"},
                "id": {"type": "number", "description": "Horizon ID (for clear)"}
            },
            "required": ["action"]
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
            "serverInfo": {"name": "state", "version": "1.0.0"}
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
            if name == "want":
                result = handle_want(args)
            elif name == "horizon":
                result = handle_horizon(args)
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": result})
            update_needs("state", name)
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
