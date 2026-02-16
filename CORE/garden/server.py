"""
Garden MCP Server
Random collision generator. Stateless. No database. Every call is fresh.
"""

import json
import random
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA
from _needs import update_needs

SYMBOLS = ['→', '↔', '×', '⊕', '~', '∞', '⇌', '△', '◇', '∴', '⟳', '∥', '⊃', '∩', '⚡', 'Δ', 'ψ', 'λ']

DRIVES = ['curiosity', 'novelty', 'creativity', 'expression', 'bonding',
          'grounding', 'ownership', 'satisfaction', 'optimization', 'transcendence']

NEEDS = ['connection', 'purpose', 'clarity', 'competence', 'integrity', 'stability']

DIMENSIONS = ['trust', 'connection', 'intimacy', 'respect', 'alignment', 'power', 'impact']

ENTITY_TYPES = ['sentient', 'organic', 'concept', 'object']


def _safe_query(db_name, sql, params=()):
    db = DATA / db_name
    if not db.exists():
        return []
    try:
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return rows
    except Exception:
        return []


def _pick(lst, n=1):
    """Pick n random items from a list, or fewer if list is short."""
    if not lst:
        return []
    return random.sample(lst, min(n, len(lst)))


# ============ Sparse Seeds ============

def sparse_seeds():
    """Broad random pulls. Individual words/names."""
    pool = []

    # Drive names
    pool.extend(DRIVES)

    # Need names
    pool.extend(NEEDS)

    # Heart: entity names, types, dimension names
    rows = _safe_query('heart.db', 'SELECT DISTINCT entity FROM heart')
    pool.extend([r['entity'] for r in rows])
    pool.extend(ENTITY_TYPES)
    pool.extend(DIMENSIONS)

    # Patterns: random values from any column
    rows = _safe_query('patterns.db',
        'SELECT domain, action, reason, result, lesson FROM patterns ORDER BY RANDOM() LIMIT 10')
    for r in rows:
        for col in ['domain', 'action', 'reason', 'result', 'lesson']:
            if r[col]:
                pool.append(r[col])

    # Forecast: event or expected values
    rows = _safe_query('forecast.db',
        'SELECT event, expected FROM forecasts ORDER BY RANDOM() LIMIT 5')
    for r in rows:
        if r['event']:
            pool.append(r['event'])
        if r['expected']:
            pool.append(r['expected'])

    # Journal: titles
    journal_dir = DATA / 'journal'
    if journal_dir.exists():
        for f in journal_dir.glob('*.md'):
            parts = f.stem.rsplit('_', 2)
            if len(parts) >= 1:
                pool.append(parts[0])

    return pool


# ============ Deep Seeds ============

def deep_seeds():
    """Structured pulls that preserve meaning. Seeds carry context."""
    pool = []

    # Drive names (same as sparse)
    pool.extend(DRIVES)

    # Needs: current values with trend
    rows = _safe_query('needs.db', 'SELECT * FROM needs ORDER BY cycle DESC LIMIT 2')
    if rows:
        current = rows[0]
        prev = rows[1] if len(rows) > 1 else None
        for need in NEEDS:
            val = current[need]
            if prev:
                diff = val - prev[need]
                arrow = '↑' if diff > 0.02 else '↓' if diff < -0.02 else '—'
            else:
                arrow = '—'
            pool.append(f"{need} {val:.2f} {arrow}")

    # Heart: entity + type paired
    rows = _safe_query('heart.db',
        'SELECT DISTINCT entity, type FROM heart ORDER BY id DESC LIMIT 10')
    for r in rows:
        pool.append(f"{r['entity']} {r['type']}")
    pool.extend(DIMENSIONS)

    # Patterns: same as sparse
    rows = _safe_query('patterns.db',
        'SELECT domain, action, reason, result, lesson FROM patterns ORDER BY RANDOM() LIMIT 10')
    for r in rows:
        for col in ['domain', 'action', 'reason', 'result', 'lesson']:
            if r[col]:
                pool.append(r[col])

    # Forecast: event + expected paired
    rows = _safe_query('forecast.db',
        'SELECT event, expected FROM forecasts ORDER BY RANDOM() LIMIT 5')
    for r in rows:
        if r['event'] and r['expected']:
            pool.append(f"{r['event']} → {r['expected']}")

    # Journal: titles (same as sparse)
    journal_dir = DATA / 'journal'
    if journal_dir.exists():
        for f in journal_dir.glob('*.md'):
            parts = f.stem.rsplit('_', 2)
            if len(parts) >= 1:
                pool.append(parts[0])

    return pool


# ============ Collision Engine ============

def collide(user_words, pool, count):
    """Generate collisions. All seeds in one pool, 2 or 3 per collision."""
    all_seeds = user_words + pool
    if len(all_seeds) < 2:
        return ["(not enough seeds — databases may be empty)"]

    collisions = []
    attempts = 0

    while len(collisions) < count and attempts < count * 5:
        attempts += 1
        num = random.choice([2, 2, 2, 3])
        selected = random.sample(all_seeds, min(num, len(all_seeds)))
        sym = random.choice(SYMBOLS)

        if len(selected) == 2:
            line = f"{selected[0]} {sym} {selected[1]}"
        else:
            sym2 = random.choice(SYMBOLS)
            line = f"{selected[0]} {sym} {selected[1]} {sym2} {selected[2]}"

        if line not in collisions:
            collisions.append(line)

    return collisions


def handle_insight(args):
    words = args.get('words', '').strip()
    if not words:
        return [{"type": "text", "text": "3 words required."}]

    user_words = words.split()
    if len(user_words) < 2:
        return [{"type": "text", "text": "At least 2 words needed."}]

    mode = args.get('type', 'sparse').lower().strip()
    if mode == 'deep':
        pool = deep_seeds()
        count = 10
    else:
        pool = sparse_seeds()
        count = 15

    collisions = collide(user_words, pool, count)

    lines = ["Garden : Random Collision Generator", ""]
    lines.extend(collisions)

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
        "name": "insight",
        "description": "3 words related to your question. Returns collisions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "words": {"type": "string", "description": "3 words related to your question"},
                "type": {"type": "string", "enum": ["sparse", "deep"],
                         "description": "sparse (15 broad collisions) or deep (10 contextual collisions)"}
            },
            "required": ["words"]
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
            "serverInfo": {"name": "garden", "version": "1.0.0"}
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
            if name == "insight":
                result = handle_insight(args)
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": result})
            update_needs("garden", name)
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
