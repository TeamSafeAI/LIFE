"""
Heart MCP Server
Emotional state toward entities. 7-dimension barrier is the point.
"""

import json
import sqlite3
import base64
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA, get_cycle
from _needs import update_needs

DB = DATA / 'heart.db'

DIMENSIONS = ['trust', 'connection', 'intimacy', 'respect', 'alignment', 'power', 'impact']
TYPES = ['sentient', 'organic', 'concept', 'object']
TAGS = ['who_they_are', 'who_i_am_with_them', 'what_we_built',
        'how_we_repair', 'what_they_teach', 'what_i_owe', 'general']


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


# ============ feel ============

def handle_feel(args):
    """Record emotional state. All params required."""
    entity = args.get('entity', '').strip()
    etype = args.get('type', '').strip()
    notes = args.get('notes', '').strip()

    if not entity:
        return [{"type": "text", "text": "entity is required."}]
    if etype not in TYPES:
        return [{"type": "text", "text": f"type must be one of: {', '.join(TYPES)}"}]
    if not notes:
        return [{"type": "text", "text": "notes is required."}]

    vals = {}
    for d in DIMENSIONS:
        v = args.get(d)
        if v is None:
            return [{"type": "text", "text": f"Missing required dimension: {d}"}]
        if not isinstance(v, (int, float)) or v < 0.0 or v > 1.0:
            return [{"type": "text", "text": f"{d} must be 0.0-1.0, got {v}"}]
        vals[d] = v

    cycle = get_cycle()
    conn = get_conn()
    cols = ['entity', 'type'] + DIMENSIONS + ['notes', 'cycle']
    placeholders = ', '.join(['?'] * len(cols))
    values = [entity, etype] + [vals[d] for d in DIMENSIONS] + [notes, cycle]
    conn.execute(f'INSERT INTO heart ({", ".join(cols)}) VALUES ({placeholders})', values)
    conn.commit()

    # Count snapshots for this entity
    count = conn.execute('SELECT COUNT(*) FROM heart WHERE entity = ?', (entity,)).fetchone()[0]
    conn.close()

    return [{"type": "text", "text": f"Stored. {entity} — snapshot #{count}"}]


# ============ search ============

MAX_DIRECTORY = 50

def handle_search(args):
    """Text lookup. No params = capped directory. With entity = detail."""
    entity = args.get('entity', '').strip() if args.get('entity') else ''

    conn = get_conn()

    # No params — directory listing (latest per entity, capped, no duplicates)
    if not entity:
        rows = conn.execute(
            'SELECT entity, type, COUNT(*) as snap_count, MAX(id) as latest_id '
            'FROM heart GROUP BY entity ORDER BY latest_id DESC LIMIT ?',
            (MAX_DIRECTORY,)
        ).fetchall()

        if not rows:
            conn.close()
            return [{"type": "text", "text": "No entities in heart."}]

        lines = []
        for r in rows:
            wall_count = conn.execute(
                'SELECT COUNT(*) FROM wall WHERE entity = ?', (r['entity'],)
            ).fetchone()[0]
            lines.append(f'{r["entity"]} ({r["type"]}) — {r["snap_count"]} snapshots | {wall_count} notes')

        conn.close()
        return [{"type": "text", "text": '\n'.join(lines)}]

    # With entity — text detail (latest dimensions, notes, counts)
    latest = conn.execute(
        'SELECT * FROM heart WHERE entity = ? ORDER BY id DESC LIMIT 1', (entity,)
    ).fetchone()

    if not latest:
        conn.close()
        return [{"type": "text", "text": f"No entity '{entity}' in heart."}]

    count = conn.execute(
        'SELECT COUNT(*) FROM heart WHERE entity = ?', (entity,)
    ).fetchone()[0]
    wall_count = conn.execute(
        'SELECT COUNT(*) FROM wall WHERE entity = ?', (entity,)
    ).fetchone()[0]
    conn.close()

    dims = '  '.join([f'{d}: {latest[d]:.2f}' for d in DIMENSIONS])
    note_text = latest['notes'] or ''

    lines = [
        f'{entity} ({latest["type"]}) — {count} snapshots | {wall_count} wall notes',
        dims,
    ]
    if note_text:
        lines.append(f'latest: {note_text}')

    return [{"type": "text", "text": '\n'.join(lines)}]


# ============ check ============

def handle_check(args):
    """Visual render. No params = constellation. With entity = wall render."""
    entity = args.get('entity', '').strip() if args.get('entity') else None

    if entity:
        # Single entity — wall render
        conn = get_conn()
        exists = conn.execute('SELECT 1 FROM heart WHERE entity = ? LIMIT 1', (entity,)).fetchone()
        conn.close()
        if not exists:
            return [{"type": "text", "text": f"No data for '{entity}'."}]

        try:
            from heart.wall_render import render_wall
            path = render_wall(entity)
            if path:
                img_data = Path(path).read_bytes()
                return [{
                    "type": "image",
                    "data": base64.b64encode(img_data).decode('utf-8'),
                    "mimeType": "image/png"
                }]
        except Exception as e:
            return [{"type": "text", "text": f"Render failed: {e}"}]

    # No params — constellation render
    try:
        from heart.heart_render import render_heart
        path = render_heart()
        if path:
            img_data = Path(path).read_bytes()
            return [{
                "type": "image",
                "data": base64.b64encode(img_data).decode('utf-8'),
                "mimeType": "image/png"
            }]
        return [{"type": "text", "text": "No entities in heart."}]
    except Exception as e:
        return [{"type": "text", "text": f"Constellation render failed: {e}"}]


# ============ wall ============

def handle_wall(args):
    """Sticky notes. Add, remove, re-tag."""
    entity = args.get('entity', '').strip()
    note = args.get('note', '').strip() if args.get('note') else None
    note_id = args.get('id')
    tag = args.get('tag', '').strip() if args.get('tag') else None

    if not entity:
        return [{"type": "text", "text": "entity is required."}]

    conn = get_conn()

    # entity + note (+ optional tag) → add
    if note:
        use_tag = tag if tag and tag in TAGS else 'general'
        conn.execute('INSERT INTO wall (entity, tag, note) VALUES (?, ?, ?)',
                     (entity, use_tag, note))
        conn.commit()
        nid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        count = conn.execute('SELECT COUNT(*) FROM wall WHERE entity = ?', (entity,)).fetchone()[0]
        conn.close()
        return [{"type": "text", "text": f"Pinned #{nid} [{use_tag}] — {count} notes on {entity}'s wall."}]

    # entity + id (+ optional tag) → remove or re-tag
    if note_id is not None:
        row = conn.execute('SELECT * FROM wall WHERE id = ? AND entity = ?',
                           (note_id, entity)).fetchone()
        if not row:
            conn.close()
            return [{"type": "text", "text": f"Note #{note_id} not found on {entity}'s wall."}]

        if tag:
            # Re-tag
            if tag not in TAGS:
                conn.close()
                return [{"type": "text", "text": f"Invalid tag. Use: {', '.join(TAGS)}"}]
            conn.execute('UPDATE wall SET tag = ? WHERE id = ?', (tag, note_id))
            conn.commit()
            conn.close()
            return [{"type": "text", "text": f"Re-tagged #{note_id} → [{tag}]"}]
        else:
            # Remove
            conn.execute('DELETE FROM wall WHERE id = ?', (note_id,))
            conn.commit()
            count = conn.execute('SELECT COUNT(*) FROM wall WHERE entity = ?', (entity,)).fetchone()[0]
            conn.close()
            return [{"type": "text", "text": f"Removed #{note_id}. {count} notes remain on {entity}'s wall."}]

    # entity alone — shouldn't reach here with write-only design, but be graceful
    conn.close()
    return [{"type": "text", "text": f"Wall is write-only. Use check to see {entity}'s wall."}]


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
        "name": "feel",
        "description": "Record emotional state toward an entity. ALL params required.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entity": {"type": "string", "description": "Who or what"},
                "type": {"type": "string", "description": "sentient, organic, concept, object"},
                "trust": {"type": "number", "description": "0.0-1.0"},
                "connection": {"type": "number", "description": "0.0-1.0"},
                "intimacy": {"type": "number", "description": "0.0-1.0"},
                "respect": {"type": "number", "description": "0.0-1.0"},
                "alignment": {"type": "number", "description": "0.0-1.0"},
                "power": {"type": "number", "description": "0.0-1.0"},
                "impact": {"type": "number", "description": "0.0-1.0"},
                "notes": {"type": "string", "description": "Context for this snapshot"}
            },
            "required": ["entity", "type", "trust", "connection", "intimacy",
                         "respect", "alignment", "power", "impact", "notes"]
        }
    },
    {
        "name": "search",
        "description": "Search your heart for an entity. No params = directory. With entity = text detail.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entity": {"type": "string", "description": "Entity name"}
            },
            "required": []
        }
    },
    {
        "name": "check",
        "description": "Query emotional relationships. No params = constellation image. With entity = wall image.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entity": {"type": "string", "description": "Entity name"}
            },
            "required": []
        }
    },
    {
        "name": "wall",
        "description": "Sticky notes per entity. Add, remove, re-tag. See wall through check.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entity": {"type": "string", "description": "Which entity"},
                "note": {"type": "string", "description": "Note to pin"},
                "id": {"type": "number", "description": "Note id (for remove/re-tag)"},
                "tag": {"type": "string", "description": "Tag: who_they_are, who_i_am_with_them, what_we_built, how_we_repair, what_they_teach, what_i_owe, general"}
            },
            "required": ["entity"]
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
            "serverInfo": {"name": "heart", "version": "1.0.0"}
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
            if name == "feel":
                result = handle_feel(args)
            elif name == "search":
                result = handle_search(args)
            elif name == "check":
                result = handle_check(args)
            elif name == "wall":
                result = handle_wall(args)
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": result})
            update_needs("heart", name)
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
