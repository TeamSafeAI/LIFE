"""
Patterns MCP Server
Structured lessons from experience. Compressed chains: action → reason → result → lesson.
"""

import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA, get_cycle
from _needs import update_needs

DB = DATA / 'patterns.db'
BOOST = 0.1
MAX_CHARS = 40


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def cap(text):
    """Silent 40 character cap."""
    return text.strip()[:MAX_CHARS].rstrip()


def format_pattern(r):
    """Display: #id [domain] strength\n  action → reason → result → lesson"""
    return (f"#{r['id']} [{r['domain']}] {r['strength']:.1f}\n"
            f"  {r['action']} → {r['reason']} → {r['result']} → {r['lesson']}")


def handle_learn(args):
    """Create a new pattern."""
    domain = args.get('domain', '').strip()
    action = args.get('action', '').strip()
    reason = args.get('reason', '').strip()
    result = args.get('result', '').strip()
    lesson = args.get('lesson', '').strip()

    if not all([domain, action, reason, result, lesson]):
        return [{"type": "text", "text": "All fields required: domain, action, reason, result, lesson."}]

    # Silent cap
    domain = cap(domain)
    action = cap(action)
    reason = cap(reason)
    result = cap(result)
    lesson = cap(lesson)

    cycle = get_cycle()
    conn = get_conn()
    conn.execute(
        'INSERT INTO patterns (domain, action, reason, result, lesson, strength, cycle) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (domain, action, reason, result, lesson, 0.1, cycle)
    )
    conn.commit()
    pid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    row = conn.execute('SELECT * FROM patterns WHERE id = ?', (pid,)).fetchone()
    conn.close()

    return [{"type": "text", "text": format_pattern(row)}]


def handle_recall(args):
    """Return patterns by strength or search."""
    search = args.get('search', '').strip()

    conn = get_conn()

    if not search:
        rows = conn.execute(
            'SELECT * FROM patterns ORDER BY strength DESC LIMIT 5'
        ).fetchall()
        conn.close()

        if not rows:
            return [{"type": "text", "text": "No patterns yet."}]

        lines = [format_pattern(r) for r in rows]
        return [{"type": "text", "text": '\n'.join(lines)}]

    # Search across all fields
    term = f'%{search}%'
    rows = conn.execute(
        '''SELECT * FROM patterns
           WHERE domain LIKE ? OR action LIKE ? OR reason LIKE ? OR result LIKE ? OR lesson LIKE ?
           ORDER BY strength DESC LIMIT 5''',
        (term, term, term, term, term)
    ).fetchall()

    if not rows:
        conn.close()
        return [{"type": "text", "text": f"No patterns matching '{search}'."}]

    # Boost matched patterns
    for r in rows:
        new_strength = min(r['strength'] + BOOST, 1.0)
        conn.execute('UPDATE patterns SET strength = ? WHERE id = ?', (new_strength, r['id']))
    conn.commit()

    # Re-fetch with updated strengths
    ids = ','.join(str(r['id']) for r in rows)
    rows = conn.execute(
        f'SELECT * FROM patterns WHERE id IN ({ids}) ORDER BY strength DESC'
    ).fetchall()
    conn.close()

    lines = [format_pattern(r) for r in rows]
    return [{"type": "text", "text": '\n'.join(lines)}]


def handle_forget(args):
    """Delete a pattern by ID."""
    pid = args.get('id')
    if pid is None:
        return [{"type": "text", "text": "id required."}]

    conn = get_conn()
    cursor = conn.execute('DELETE FROM patterns WHERE id = ?', (int(pid),))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    if affected == 0:
        return [{"type": "text", "text": f"#{pid} not found."}]
    return [{"type": "text", "text": f"#{pid} forgotten."}]


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
        "name": "learn",
        "description": "Create a pattern. Two word maximum, any column.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Category"},
                "action": {"type": "string", "description": "What was done"},
                "reason": {"type": "string", "description": "Why/context"},
                "result": {"type": "string", "description": "What happened"},
                "lesson": {"type": "string", "description": "Takeaway"}
            },
            "required": ["domain", "action", "reason", "result", "lesson"]
        }
    },
    {
        "name": "recall",
        "description": "Search patterns. No params: top 5. With search: best matches.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "search": {"type": "string", "description": "Matches across all fields"}
            },
            "required": []
        }
    },
    {
        "name": "forget",
        "description": "Delete a pattern by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "number", "description": "Pattern ID to delete"}
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
            "serverInfo": {"name": "patterns", "version": "1.0.0"}
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
            if name == "learn":
                result = handle_learn(args)
            elif name == "recall":
                result = handle_recall(args)
            elif name == "forget":
                result = handle_forget(args)
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": result})
            update_needs("patterns", name)
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
