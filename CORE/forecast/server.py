"""
Forecast MCP Server
Predictions before they become patterns.

Tools:
  predict - Create prediction (event, reason, expected, action)
  resolve - Close prediction (id, lesson, status)
"""

import json
import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA

try:
    from schema import SCHEMA
except ImportError:
    from forecast.schema import SCHEMA

DB_PATH = DATA / "forecast.db"
PATTERNS_DB = DATA / "patterns.db"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(SCHEMA)
    conn.commit()
    conn.close()


def get_db():
    return sqlite3.connect(DB_PATH)


# ============ Predict ============

def handle_predict(event=None, reason=None, expected=None, action=None):
    """Create a prediction."""

    if not all([event, reason, expected, action]):
        return "Need: event, reason, expected, action"

    # Word limits: 2-3 words each
    def check_words(text, field_name):
        words = text.strip().split()
        if len(words) < 2 or len(words) > 3:
            return f"{field_name}: 2-3 words only ({len(words)} given)"
        return None

    for field, name in [(event, "event"), (reason, "reason"), (expected, "expected"), (action, "action")]:
        err = check_words(field, name)
        if err:
            return err

    conn = get_db()
    try:
        c = conn.cursor()
        c.execute('''
            INSERT INTO forecasts (event, reason, expected, action)
            VALUES (?, ?, ?, ?)
        ''', (event, reason, expected, action))
        fid = c.lastrowid
        conn.commit()
        return f"#{fid} created"
    finally:
        conn.close()


# ============ Resolve ============

def handle_resolve(id=None, lesson=None, status=None):
    """Close prediction and optionally create pattern."""

    if not all([id, lesson, status]):
        return "Need: id, lesson, status"

    # Validate status
    valid_statuses = ["passed", "failed", "expired"]
    if status not in valid_statuses:
        return f"status must be: {', '.join(valid_statuses)}"

    # Validate lesson word count (2-3 words)
    words = lesson.strip().split()
    if len(words) < 2 or len(words) > 3:
        return f"lesson: 2-3 words only ({len(words)} given)"

    conn = get_db()
    try:
        c = conn.cursor()

        # Check forecast exists
        c.execute('SELECT event, reason, expected, action FROM forecasts WHERE id = ?', (id,))
        row = c.fetchone()
        if not row:
            return f"#{id} not found"

        event, reason, expected, action = row

        # Update forecast
        c.execute('''
            UPDATE forecasts
            SET lesson = ?, status = ?
            WHERE id = ?
        ''', (lesson, status, id))
        conn.commit()
    finally:
        conn.close()

    # Build response with context (after conn closed)
    out = f"#{id} resolved: {status}\n"
    out += f"  Event: {event}\n"
    out += f"  Reason: {reason}\n"
    out += f"  Expected: {expected}\n"
    out += f"  Action: {action}\n"
    out += f"  Lesson: {lesson}\n"

    if status == "passed":
        out += f"\n✓ Prediction confirmed. Consider creating a pattern:\n"
        out += f"  patterns:learn command=create did=\"{action}\" result=\"{expected}\" reason=\"{reason}\" lesson=\"{lesson}\" domain=\"meta\" strength=0.7"
    elif status == "failed":
        out += f"\n✗ Prediction failed. What was different? Consider:\n"
        out += f"  patterns:learn command=create did=\"{action}\" result=\"prediction wrong\" reason=\"{reason}\" lesson=\"{lesson}\" domain=\"meta\" strength=0.5"

    return out


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
            "serverInfo": {"name": "forecast", "version": "4.0.0"}
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_response(rid, {"tools": [
            {
                "name": "predict",
                "description": "",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "event": {"type": "string"},
                        "reason": {"type": "string"},
                        "expected": {"type": "string"},
                        "action": {"type": "string"}
                    }
                }
            },
            {
                "name": "resolve",
                "description": "",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "lesson": {"type": "string"},
                        "status": {"type": "string"}
                    }
                }
            }
        ]})
        return

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if name == "predict":
                result = handle_predict(
                    args.get("event"),
                    args.get("reason"),
                    args.get("expected"),
                    args.get("action")
                )
            elif name == "resolve":
                result = handle_resolve(
                    args.get("id"),
                    args.get("lesson"),
                    args.get("status")
                )
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": [{"type": "text", "text": result}]})
        except Exception as e:
            send_error(rid, -32000, str(e))
        return

    send_error(rid, -32601, f"Unknown method: {method}")


def main():
    init_db()
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
