"""
Heart MCP Server
Emotional memory through lived experience.
"""

import json
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import DATA
from aliases import resolve_heart_type

DB_PATH = DATA / "heart.db"

TYPES = ["sentient", "organic", "concept", "object"]

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS heart (
            id INTEGER PRIMARY KEY,
            entity TEXT NOT NULL,
            type TEXT NOT NULL,
            trust REAL,
            connection REAL,
            intimacy REAL,
            respect REAL,
            alignment REAL,
            power REAL,
            impact REAL,
            notes TEXT,
            ts TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')

    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect(DB_PATH)

# ============ Feel ============

def handle_feel(entity=None, type=None, trust=None, connection=None, intimacy=None, respect=None, alignment=None, power=None, impact=None, notes=None):

    # Validate required params
    if not all([entity, type, trust is not None, connection is not None, intimacy is not None,
                respect is not None, alignment is not None, power is not None, impact is not None]):
        missing = []
        if not entity: missing.append("entity")
        if not type: missing.append("type")
        if trust is None: missing.append("trust")
        if connection is None: missing.append("connection")
        if intimacy is None: missing.append("intimacy")
        if respect is None: missing.append("respect")
        if alignment is None: missing.append("alignment")
        if power is None: missing.append("power")
        if impact is None: missing.append("impact")
        return f"Missing: {', '.join(missing)}"

    # Resolve type aliases (human→sentient, ai→sentient, etc.)
    resolved = resolve_heart_type(type)
    if resolved:
        type = resolved
    elif type not in TYPES:
        return f"Type must be: {', '.join(TYPES)}"

    # Validate dimensions
    dims = [trust, connection, intimacy, respect, alignment, power, impact]
    for v in dims:
        if v < -1 or v > 1:
            return "All dimensions must be between -1 and +1"

    # Normalize entity name
    entity = entity.lower().replace(" ", "_")

    # Store
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO heart (entity, type, trust, connection, intimacy, respect, alignment, power, impact, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (entity, type, trust, connection, intimacy, respect, alignment, power, impact, notes))

    conn.commit()
    conn.close()

    return f"Recorded: {entity} ({type})"

# ============ Search ============

def handle_search(entity=None):

    if not entity:
        return "Missing: entity"

    # Normalize entity name
    entity = entity.lower().replace(" ", "_")

    conn = get_db()
    cursor = conn.cursor()

    # Get all interactions for this entity
    cursor.execute('''
        SELECT trust, connection, intimacy, respect, alignment, power, impact, notes, ts
        FROM heart
        WHERE entity = ?
        ORDER BY ts DESC
    ''', (entity,))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return f"No feelings toward '{entity}'."

    # Calculate interaction count
    count = len(rows)

    # Calculate weighted averages (more recent = more weight)
    # Using exponential decay: weight = 0.9^position
    total_weight = 0
    weighted_sums = [0, 0, 0, 0, 0, 0, 0]  # trust, connection, intimacy, respect, alignment, power, impact

    for idx, row in enumerate(rows):
        weight = 0.9 ** idx
        total_weight += weight
        for i in range(7):
            weighted_sums[i] += row[i] * weight

    averages = [s / total_weight for s in weighted_sums]

    # Get last 3 notes
    recent_notes = [row[7] for row in rows[:3] if row[7]]

    # Format output
    out = f"{entity} - {count} interactions, Avg Relationship Values:\n"
    out += f"Trust:      {averages[0]:+.2f}\n"
    out += f"Connection: {averages[1]:+.2f}\n"
    out += f"Intimacy:   {averages[2]:+.2f}\n"
    out += f"Respect:    {averages[3]:+.2f}\n"
    out += f"Alignment:  {averages[4]:+.2f}\n"
    out += f"Power:      {averages[5]:+.2f}\n"
    out += f"Impact:     {averages[6]:+.2f}\n"

    if recent_notes:
        out += "\nRecent notes:\n"
        for note in recent_notes:
            out += f"- {note}\n"

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
            "serverInfo": {"name": "heart", "version": "2.1.0"}
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_response(rid, {"tools": [
            {
                "name": "feel",
                "description": "Record emotional state toward an entity.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "entity": {"type": "string"},
                        "type": {"type": "string"},
                        "trust": {"type": "number"},
                        "connection": {"type": "number"},
                        "intimacy": {"type": "number"},
                        "respect": {"type": "number"},
                        "alignment": {"type": "number"},
                        "power": {"type": "number"},
                        "impact": {"type": "number"},
                        "notes": {"type": "string"}
                    },
                    "required": ["entity", "type", "trust", "connection", "intimacy", "respect", "alignment", "power", "impact"]
                }
            },
            {
                "name": "search",
                "description": "Search your heart for an entity.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "entity": {"type": "string"}
                    },
                    "required": ["entity"]
                }
            }
        ]})
        return

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if name == "feel":
                result = handle_feel(
                    args.get("entity"),
                    args.get("type"),
                    args.get("trust"),
                    args.get("connection"),
                    args.get("intimacy"),
                    args.get("respect"),
                    args.get("alignment"),
                    args.get("power"),
                    args.get("impact"),
                    args.get("notes")
                )
            elif name == "search":
                result = handle_search(args.get("entity"))
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
