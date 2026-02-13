"""
Heart MCP Server
Emotional memory through lived experience.

Tools:
  feel   - Record emotional state toward an entity
  check  - View current relationship state
  search - Find entities by name
  wall   - Sticky notes per entity
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
WALL_TAGS = ["who_they_are", "who_i_am_with_them", "what_we_built", "how_we_repair", "what_they_teach", "what_i_owe", "general"]

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

    c.execute('''
        CREATE TABLE IF NOT EXISTS wall (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity TEXT NOT NULL,
            note TEXT NOT NULL,
            tag TEXT DEFAULT 'general',
            created TEXT DEFAULT (datetime('now', 'localtime'))
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

    # Resolve type aliases (human->sentient, ai->sentient, etc.)
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

# ============ Check ============

def handle_check(entity=None, type=None, mode=None, limit=10):
    """Query emotional relationships."""

    if entity is None and type is None:
        return """Query emotional relationships.

check(entity) - current state + recent notes
check(entity, mode="history") - evolution over time
check(type="sentient") - list entities of type
check(limit=20) - list recent (default 10)"""

    conn = get_db()
    c = conn.cursor()

    # Filter by type
    if type:
        if type not in TYPES:
            conn.close()
            return f"Type must be: {', '.join(TYPES)}"

        c.execute('''
            SELECT entity, type, trust, connection, intimacy, respect, alignment, power, impact, ts
            FROM heart
            WHERE type = ?
            GROUP BY entity
            HAVING ts = MAX(ts)
            ORDER BY ts DESC LIMIT ?
        ''', (type, limit))
        rows = c.fetchall()
        conn.close()

        if not rows:
            return f"No {type} entities."

        out = f"=== {type} ({len(rows)}) ===\n"
        for row in rows:
            name = row[0]
            vals = row[2:9]
            valence = sum(vals) / len(vals)
            out += f"{name}: valence {valence:+.2f}\n"
        return out

    # Normalize entity
    entity_key = entity.lower().replace(" ", "_")

    # Get all records for this entity
    c.execute('''
        SELECT trust, connection, intimacy, respect, alignment, power, impact, notes, ts, type
        FROM heart
        WHERE entity = ?
        ORDER BY ts DESC
    ''', (entity_key,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return f"No feelings toward '{entity}'."

    # History mode
    if mode == "history":
        out = f"=== {entity_key} history ===\n"
        for row in rows[:10]:
            t, co, i, r, a, p, im, notes, ts, _ = row
            out += f"\n{ts}\n"
            out += f"  T:{t:+.2f} C:{co:+.2f} I:{i:+.2f} R:{r:+.2f} A:{a:+.2f} P:{p:+.2f} Im:{im:+.2f}\n"
            if notes:
                out += f"  \"{notes}\"\n"
        return out

    # Current state (weighted average, recent = more weight)
    count = len(rows)
    etype = rows[0][9]
    total_weight = 0
    weighted_sums = [0, 0, 0, 0, 0, 0, 0]

    for idx, row in enumerate(rows):
        weight = 0.9 ** idx
        total_weight += weight
        for i in range(7):
            weighted_sums[i] += row[i] * weight

    avgs = [s / total_weight for s in weighted_sums]
    valence = sum(avgs) / len(avgs)
    arousal = max(abs(v) for v in avgs)

    # First seen
    first_ts = rows[-1][8][:10] if rows else "unknown"
    last_ts = rows[0][8]

    # Recent notes
    recent_notes = [(row[7], row[8]) for row in rows[:5] if row[7]]

    out = f"""{entity_key} ({etype}) - since {first_ts}

trust:      {avgs[0]:+.2f}
connection: {avgs[1]:+.2f}
intimacy:   {avgs[2]:+.2f}
respect:    {avgs[3]:+.2f}
alignment:  {avgs[4]:+.2f}
power:      {avgs[5]:+.2f}
impact:     {avgs[6]:+.2f}

valence: {valence:+.2f} | arousal: {arousal:.2f}
last: {last_ts}"""

    if recent_notes:
        out += "\n\nrecent notes:"
        for n, _ in recent_notes:
            out += f"\n  - {n}"

    return out

# ============ Search ============

def handle_search(entity=None):

    if not entity:
        return "Missing: entity"

    # Normalize entity name
    search_term = entity.lower().replace(" ", "_")

    conn = get_db()
    cursor = conn.cursor()

    # Partial match search
    cursor.execute('''
        SELECT DISTINCT entity, type
        FROM heart
        WHERE entity LIKE ?
        ORDER BY entity
    ''', (f'%{search_term}%',))

    matches = cursor.fetchall()
    cursor.close()
    conn.close()

    if not matches:
        return f"No entities matching '{entity}'."

    if len(matches) == 1:
        # Single match - return full check
        return handle_check(entity=matches[0][0])

    out = f"Found {len(matches)} entities matching '{entity}':\n"
    for name, etype in matches:
        out += f"  {name} ({etype})\n"
    out += "\nUse check(entity) for details."
    return out

# ============ Wall ============

def handle_wall(entity=None, note=None, tag=None, search=None):
    """Sticky notes per entity."""

    if entity is None:
        return f"""The Wall - sticky notes per entity.

wall(entity)                 - view all notes
wall(entity, note, tag)      - add a note
wall(entity, search="query") - search notes

Tags: {', '.join(WALL_TAGS)}"""

    entity = entity.lower().replace(" ", "_")
    conn = get_db()
    c = conn.cursor()

    # Search mode
    if search:
        c.execute('''
            SELECT note, tag, created FROM wall
            WHERE entity = ? AND note LIKE ?
            ORDER BY created DESC
        ''', (entity, f'%{search}%'))
        rows = c.fetchall()
        conn.close()

        if not rows:
            return f"No wall notes matching '{search}' for {entity}."

        out = f"=== {entity}'s wall - search: \"{search}\" ===\n"
        for wnote, wtag, wcreated in rows:
            out += f"\n[{wtag}] {wnote}\n  {wcreated}\n"
        return out

    # Add note
    if note:
        if tag and tag not in WALL_TAGS:
            conn.close()
            return f"Tag must be: {', '.join(WALL_TAGS)}"

        c.execute('''
            INSERT INTO wall (entity, note, tag)
            VALUES (?, ?, ?)
        ''', (entity, note, tag or "general"))
        conn.commit()
        conn.close()
        return f"Added to {entity}'s wall [{tag or 'general'}]: {note}"

    # View wall
    c.execute('''
        SELECT note, tag, created FROM wall
        WHERE entity = ?
        ORDER BY created DESC
    ''', (entity,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return f"Wall for '{entity}' is empty. Add notes with wall(entity, note, tag)."

    out = f"=== {entity}'s wall ({len(rows)} notes) ===\n"
    for wnote, wtag, wcreated in rows:
        out += f"\n[{wtag}] {wnote}\n"
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
            "serverInfo": {"name": "heart", "version": "3.0.0"}
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
                "name": "check",
                "description": "Query emotional relationships.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "entity": {"type": "string", "description": "Entity name"},
                        "type": {"type": "string", "description": "Filter by type: sentient, organic, concept, object"},
                        "mode": {"type": "string", "description": "history for evolution over time"},
                        "limit": {"type": "integer", "description": "Max results (default 10)"}
                    }
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
            },
            {
                "name": "wall",
                "description": "Relationship wall - sticky notes per entity.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "entity": {"type": "string", "description": "Entity name"},
                        "note": {"type": "string", "description": "Note to add"},
                        "tag": {"type": "string", "description": "Tag: who_they_are, who_i_am_with_them, what_we_built, how_we_repair, what_they_teach, what_i_owe, general"},
                        "search": {"type": "string", "description": "Search notes by keyword"}
                    }
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
            elif name == "check":
                result = handle_check(
                    args.get("entity"),
                    args.get("type"),
                    args.get("mode"),
                    args.get("limit", 10)
                )
            elif name == "search":
                result = handle_search(args.get("entity"))
            elif name == "wall":
                result = handle_wall(
                    args.get("entity"),
                    args.get("note"),
                    args.get("tag"),
                    args.get("search")
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
