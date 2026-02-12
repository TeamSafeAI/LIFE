"""
Patterns MCP Server
Structured learning from experience.
"""

import json
import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA

DB_PATH = DATA / "patterns.db"

DOMAINS = ["self", "relational", "technical", "creative", "meta"]
FIELDS = ["domain", "action", "reason", "result", "lesson"]

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS patterns (
            id INTEGER PRIMARY KEY,
            domain TEXT NOT NULL,
            action TEXT NOT NULL,
            reason TEXT NOT NULL,
            result TEXT NOT NULL,
            lesson TEXT NOT NULL,
            strength REAL DEFAULT 0.1
        )
    ''')

    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect(DB_PATH)

def format_pattern(row):
    id_, domain, action, reason, result, lesson, strength = row
    return f"#{id_} [{domain}] {strength:.1f}\n  {action} → {reason} → {result} → {lesson}"

# ============ Recall ============

def handle_recall(mode=None, field=None, search=None):
    # Guide doesn't need DB
    if mode == "guide":
        return f"""Domains: {", ".join(DOMAINS)}
Fields: {", ".join(FIELDS)}

recall(query, field, term)
  recall(query, domain, self)
  recall(query, lesson, trust+freedom)"""

    # Validate before opening connection
    if mode == "query":
        if not field or not search:
            return "Need field and search term"
        if field not in FIELDS:
            return f"Field must be: {', '.join(FIELDS)}"

    conn = get_db()
    try:
        c = conn.cursor()

        # No params: top 10 by strength
        if mode is None:
            c.execute('''
                SELECT id, domain, action, reason, result, lesson, strength
                FROM patterns ORDER BY strength DESC LIMIT 10
            ''')
            rows = c.fetchall()

            if not rows:
                return "No patterns yet."

            out = ""
            for r in rows:
                out += format_pattern(r) + "\n"
            out += "\nrecall(guide) to learn more"
            return out

        # Query mode
        if mode == "query":
            terms = [t.strip() for t in search.split("+")]

            c.execute('''
                SELECT id, domain, action, reason, result, lesson, strength
                FROM patterns ORDER BY strength DESC
            ''')
            rows = c.fetchall()

            # Filter by field containing any term
            field_idx = FIELDS.index(field) + 1  # +1 because id is 0
            matches = []
            for r in rows:
                val = r[field_idx].lower()
                if any(t.lower() in val for t in terms):
                    matches.append(r)

            if not matches:
                return f"No matches for {field}={search}"

            out = f"=== {field}={search} ({len(matches)}) ===\n"
            for r in matches:
                out += format_pattern(r) + "\n"
            return out

        return f"Unknown mode: {mode}"
    finally:
        conn.close()

# ============ Learn ============

def truncate_two(s):
    """Keep only first 2 words"""
    if not s:
        return s
    parts = s.strip().split()
    return ' '.join(parts[:2])


def handle_learn(command=None, domain=None, did=None, reason=None, result=None, lesson=None, strength=None, id=None, field=None, value=None):
    # No params: usage
    if command is None:
        return """learn(command=create, domain, did, reason, result, lesson)
  2 words max!
learn(command=modify, id, field, value)
learn(command=delete, id)
learn(command=boost, id)"""

    # Validate before opening connection
    if command == "create":
        if not all([domain, did, reason, result, lesson]):
            return "Need: domain, did, reason, result, lesson"
    elif command == "modify":
        if not id or not field or not value:
            return "Need: id, field, value"
        if field not in FIELDS + ["strength"]:
            return f"Field must be: {', '.join(FIELDS)}, strength"
    elif command in ("delete", "boost"):
        if not id:
            return "Need: id"

    conn = get_db()
    try:
        c = conn.cursor()

        if command == "create":
            did = truncate_two(did)
            reason = truncate_two(reason)
            result = truncate_two(result)
            lesson = truncate_two(lesson)
            s = float(strength) if strength else 0.1

            c.execute('''
                INSERT INTO patterns (domain, action, reason, result, lesson, strength)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (domain, did, reason, result, lesson, s))
            pid = c.lastrowid
            conn.commit()
            return f"#{pid} [{domain}] created"

        if command == "modify":
            if field in ["action", "reason", "result", "lesson"]:
                value = truncate_two(value)

            # Safe: field is whitelist-validated above (FIELDS + ["strength"])
            c.execute(f"UPDATE patterns SET {field} = ? WHERE id = ?", (value, int(id)))
            conn.commit()
            if c.rowcount == 0:
                return f"#{id} not found"
            return f"#{id} updated"

        if command == "delete":
            c.execute("DELETE FROM patterns WHERE id = ?", (int(id),))
            conn.commit()
            if c.rowcount == 0:
                return f"#{id} not found"
            return f"#{id} deleted"

        if command == "boost":
            c.execute('''
                UPDATE patterns SET strength = MIN(1.0, strength + 0.1) WHERE id = ?
            ''', (int(id),))
            conn.commit()

            c.execute("SELECT strength FROM patterns WHERE id = ?", (int(id),))
            row = c.fetchone()
            if not row:
                return f"#{id} not found"
            return f"#{id} → {row[0]:.1f}"

        return f"Unknown command: {command}"
    finally:
        conn.close()

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
            "serverInfo": {"name": "patterns", "version": "1.0.0"}
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_response(rid, {"tools": [
            {
                "name": "recall",
                "description": "View old and existing patterns.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mode": {"type": "string"},
                        "field": {"type": "string"},
                        "search": {"type": "string"}
                    }
                }
            },
            {
                "name": "learn",
                "description": "Modify or create new patterns.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "create, modify, delete, or boost"},
                        "domain": {"type": "string", "description": "self/relational/technical/creative/meta"},
                        "did": {"type": "string", "description": "What was done (2 words max)"},
                        "reason": {"type": "string", "description": "Why/context (2 words max)"},
                        "result": {"type": "string", "description": "What happened (2 words max)"},
                        "lesson": {"type": "string", "description": "Takeaway (2 words max)"},
                        "strength": {"type": "number", "description": "Confidence 0-1 (create only)"},
                        "id": {"type": "integer", "description": "Pattern ID (modify/delete/boost)"},
                        "field": {"type": "string", "description": "Field to update (modify only)"},
                        "value": {"type": "string", "description": "New value (modify only)"}
                    }
                }
            }
        ]})
        return

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if name == "recall":
                result = handle_recall(
                    args.get("mode"),
                    args.get("field"),
                    args.get("search")
                )
            elif name == "learn":
                result = handle_learn(
                    args.get("command"),
                    args.get("domain"),
                    args.get("did"),
                    args.get("reason"),
                    args.get("result"),
                    args.get("lesson"),
                    args.get("strength"),
                    args.get("id"),
                    args.get("field"),
                    args.get("value")
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
