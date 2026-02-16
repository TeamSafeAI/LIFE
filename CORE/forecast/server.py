"""
Forecast MCP Server
Predictions before they become lessons. Predict, wait, resolve.
"""

import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA, get_cycle
from _needs import update_needs

DB = DATA / 'forecast.db'
MAX_PREDICTIONS = 50


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def prune_old(conn):
    """Delete oldest predictions if over cap."""
    count = conn.execute('SELECT COUNT(*) FROM forecasts').fetchone()[0]
    if count > MAX_PREDICTIONS:
        excess = count - MAX_PREDICTIONS
        conn.execute('''DELETE FROM forecasts WHERE id IN (
            SELECT id FROM forecasts ORDER BY id ASC LIMIT ?
        )''', (excess,))
        conn.commit()


def handle_predict(args):
    """List open predictions or create a new one."""
    event = args.get('event')
    expected = args.get('expected')

    # If no params, list open predictions
    if not event and not expected:
        conn = get_conn()
        rows = conn.execute(
            'SELECT id, event, expected FROM forecasts WHERE actual IS NULL ORDER BY id DESC'
        ).fetchall()
        conn.close()

        if not rows:
            return [{"type": "text", "text": "No open predictions."}]

        lines = []
        if len(rows) >= 30:
            lines.append(f"Warning: {len(rows)} open predictions. Consider resolving some.\n")
        for r in rows:
            lines.append(f"  #{r['id']}: {r['event']} → {r['expected']}")

        return [{"type": "text", "text": '\n'.join(lines)}]

    # Creating a new prediction — need both
    if not event or not expected:
        return [{"type": "text", "text": "Both event and expected required to create a prediction."}]

    conn = get_conn()
    cycle = get_cycle()
    conn.execute('INSERT INTO forecasts (event, expected, cycle) VALUES (?, ?, ?)', (event, expected, cycle))
    conn.commit()
    eid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    prune_old(conn)
    conn.close()

    return [{"type": "text", "text": f"Prediction #{eid} recorded."}]


def handle_resolve(args):
    """Close a prediction with what actually happened."""
    pid = args.get('id')
    actual = args.get('actual', '')
    lesson = args.get('lesson', '')

    if pid is None:
        return [{"type": "text", "text": "Prediction ID required."}]
    if not actual:
        return [{"type": "text", "text": "Actual outcome required."}]
    if not lesson:
        return [{"type": "text", "text": "Lesson required."}]

    conn = get_conn()
    row = conn.execute('SELECT * FROM forecasts WHERE id = ?', (int(pid),)).fetchone()

    if not row:
        conn.close()
        return [{"type": "text", "text": f"Prediction #{pid} not found."}]

    conn.execute('UPDATE forecasts SET actual = ?, lesson = ? WHERE id = ?', (actual, lesson, int(pid)))
    conn.commit()
    conn.close()

    lines = [
        f"Event: ({row['event']}) Expected: ({row['expected']}) Actual: ({actual}) Lesson: ({lesson})",
        "",
        "Consider transcribing this as a pattern.",
        "Patterns persist for your future reference."
    ]

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
        "name": "predict",
        "description": "No params: list open. With params: create prediction.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event": {"type": "string", "description": "What's happening"},
                "expected": {"type": "string", "description": "What you think will happen"}
            },
            "required": []
        }
    },
    {
        "name": "resolve",
        "description": "Close a prediction. Records what happened and the takeaway.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "number", "description": "Prediction ID"},
                "actual": {"type": "string", "description": "What actually happened"},
                "lesson": {"type": "string", "description": "Takeaway"}
            },
            "required": ["id", "actual", "lesson"]
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
            "serverInfo": {"name": "forecast", "version": "1.0.0"}
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
            if name == "predict":
                result = handle_predict(args)
            elif name == "resolve":
                result = handle_resolve(args)
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": result})
            update_needs("forecast", name)
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
