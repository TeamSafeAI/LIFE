"""
Think MCP Server v6
Multi-stream cognitive capture with context enrichment.

Tools:
  stream  - Capture cognitive state (3+ streams, 2-3 words each)
  recent  - Show recent thought captures
  search  - Search thought history by content
"""

import json
import sys
import sqlite3
import random
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import CORE, DATA

# Garden feeder - populates garden seeds on each stream capture
try:
    from garden_feeder import feed_all as feed_garden
except Exception:
    feed_garden = None

DB_PATH = DATA / "think.db"
HEART_DB = DATA / "heart.db"
PATTERNS_DB = DATA / "patterns.db"
SEMANTIC_DB = DATA / "semantic.db"
IDENTITY_DB = DATA / "identity.db"
WORKING_DB = DATA / "working.db"
GARDEN_PATH = CORE / "garden"

# Known streams (guidance, not enforcement — custom streams allowed)
KNOWN_STREAMS = [
    "meta", "cognitive", "analytical", "creative", "relational",
    "predictive", "embodied", "autonomic", "vision", "hearing"
]

MIN_STREAMS = 3
MAX_WORDS = 4  # soft limit (warn at 4, reject at 6)


# ============ DB Init ============

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS thoughts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT (datetime('now', 'localtime'))
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS thought_streams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thought_id INTEGER REFERENCES thoughts(id),
            stream TEXT NOT NULL,
            value TEXT NOT NULL,
            context TEXT
        )
    ''')

    c.execute('CREATE INDEX IF NOT EXISTS idx_thought_id ON thought_streams(thought_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_stream ON thought_streams(stream)')

    conn.commit()
    conn.close()


def get_db():
    return sqlite3.connect(DB_PATH)


# ============ Context Pull Functions ============

def pull_meta(input_text):
    """Return last 3 think entries (self-reference)."""
    conn = get_db()
    c = conn.cursor()

    c.execute('SELECT id, timestamp FROM thoughts ORDER BY id DESC LIMIT 3')
    thought_rows = c.fetchall()

    if not thought_rows:
        conn.close()
        return None

    results = []
    for t_id, ts in thought_rows:
        time_str = ts[11:16] if ts else "?"
        c.execute('SELECT stream, value FROM thought_streams WHERE thought_id = ?', (t_id,))
        streams = c.fetchall()
        # Use cognitive as title, or first stream
        title = "untitled"
        parts = []
        for stream, value in streams:
            if stream == "cognitive":
                title = value
            else:
                parts.append(f"{stream}:{value}")
        summary = " | ".join(parts[:3]) if parts else "-"
        results.append(f"#{t_id} [{time_str}] {title}: {summary}")

    conn.close()
    return results


def pull_relational(input_text):
    """Search heart entities by each word, return notes."""
    if not HEART_DB.exists():
        return None

    words = input_text.lower().split()
    results = []

    conn = sqlite3.connect(HEART_DB)
    c = conn.cursor()

    for word in words:
        c.execute('''
            SELECT e.name, h.notes
            FROM entity e
            JOIN heart h ON e.id = h.entity_id
            WHERE LOWER(e.name) LIKE ?
            ORDER BY h.ts DESC LIMIT 1
        ''', (f'%{word}%',))
        row = c.fetchone()
        if row and row[1]:
            results.append(f"{row[0]}: {row[1]}")

    conn.close()
    return results if results else None


def pull_analytical(input_text):
    """Search patterns by keyword, return full pattern."""
    if not PATTERNS_DB.exists():
        return None

    words = input_text.lower().split()
    results = []
    seen_ids = set()

    conn = sqlite3.connect(PATTERNS_DB)
    c = conn.cursor()

    for word in words:
        # Search across action, reason, result, lesson
        for field in ['reason', 'action', 'result', 'lesson']:
            c.execute(f'''
                SELECT id, domain, action, reason, result, lesson, strength
                FROM patterns
                WHERE LOWER({field}) LIKE ?
                ORDER BY strength DESC
            ''', (f'%{word}%',))
            for row in c.fetchall():
                if row[0] not in seen_ids:
                    seen_ids.add(row[0])
                    id_, domain, action, reason, result, lesson, strength = row
                    results.append(f"#{id_} [{domain}] {strength:.1f}: {action} \u2192 {reason} \u2192 {result} \u2192 {lesson}")

    conn.close()
    return results[:5] if results else None  # Cap at 5


def pull_predictive(input_text):
    """Search semantic memory titles, return summary. Refreshes accessed memories."""
    if not SEMANTIC_DB.exists():
        return None

    words = input_text.lower().split()
    results = []
    seen_ids = set()

    conn = sqlite3.connect(SEMANTIC_DB)
    c = conn.cursor()

    for word in words:
        c.execute('''
            SELECT id, title, summary
            FROM memories
            WHERE LOWER(title) LIKE ?
            ORDER BY created DESC LIMIT 2
        ''', (f'%{word}%',))
        for row in c.fetchall():
            if row[0] not in seen_ids:
                seen_ids.add(row[0])
                results.append(f"[{row[0]}] {row[1]}: {row[2]}")
                # Reinforce: update last_accessed so decay knows this memory is relevant
                c.execute('''
                    UPDATE memories
                    SET last_accessed = datetime('now', 'localtime')
                    WHERE id = ?
                ''', (row[0],))

    conn.commit()
    conn.close()
    return results[:5] if results else None


def pull_autonomic(input_text):
    """Return hot working memory threads."""
    if not WORKING_DB.exists():
        return None

    conn = sqlite3.connect(WORKING_DB)
    c = conn.cursor()

    c.execute('''
        SELECT id, title, last_touched
        FROM topics
        WHERE archived = 0
        AND datetime(last_touched) > datetime('now', '-1 day', 'localtime')
        ORDER BY last_touched DESC LIMIT 5
    ''')
    rows = c.fetchall()
    conn.close()

    if not rows:
        return None

    return [f"#{id_} {title}" for id_, title, _ in rows]


def pull_embodied(input_text):
    """Return current drive values."""
    if not IDENTITY_DB.exists():
        return None

    conn = sqlite3.connect(IDENTITY_DB)
    c = conn.cursor()

    try:
        # Get drive column names
        c.execute("PRAGMA table_info(drives)")
        cols = c.fetchall()
        skip = {'id', 'cycle', 'timestamp', 'reflection'}
        drive_cols = [col[1] for col in cols if col[1] not in skip]

        if not drive_cols:
            conn.close()
            return None

        c.execute(f'SELECT {", ".join(drive_cols)} FROM drives ORDER BY id DESC LIMIT 1')
        row = c.fetchone()
        conn.close()

        if not row:
            return None

        # Only show drives relevant to input words, or all if no match
        words = input_text.lower().split()
        results = []
        for i, name in enumerate(drive_cols):
            value = row[i]
            if any(w in name for w in words) or not words:
                bar = "\u2588" * int(value * 10) + "\u2591" * (10 - int(value * 10))
                results.append(f"{name}: {bar} {value:.2f}")

        # If no word matches, show top 3 by value
        if not results:
            sorted_drives = sorted(zip(drive_cols, row), key=lambda x: x[1], reverse=True)
            for name, value in sorted_drives[:3]:
                bar = "\u2588" * int(value * 10) + "\u2591" * (10 - int(value * 10))
                results.append(f"{name}: {bar} {value:.2f}")

        return results

    except Exception:
        conn.close()
        return None


def pull_creative(input_text):
    """Generate collisions via garden's collision engine.

    Delegates to garden server's public API instead of reimplementing.
    Falls back to basic collision if garden module unavailable.
    """
    try:
        # Import garden's public API
        garden_path = str(GARDEN_PATH)
        if garden_path not in sys.path:
            sys.path.insert(0, garden_path)
        from server import get_collisions_for_think
        return get_collisions_for_think(input_text, count=3)
    except Exception:
        # Fallback: basic collision from garden.db directly
        garden_db = DATA / "garden.db"
        if not garden_db.exists():
            return None

        try:
            conn = sqlite3.connect(garden_db)
            c = conn.cursor()
            c.execute('SELECT seed, source FROM seeds ORDER BY last_hit DESC LIMIT 30')
            rows = c.fetchall()
            conn.close()

            if len(rows) < 2:
                return None

            input_words = [w.strip().lower() for w in input_text.split()]
            symbols = ["→", "↔", "×", "⊕", "~", "⇌", "△", "◇", "∴"]
            results = []

            for _ in range(3):
                seed, source = random.choice(rows)
                sym = random.choice(symbols)
                if input_words:
                    iw = random.choice(input_words)
                    results.append(f"{iw} {sym} {seed} (from: input, {source})")
                elif len(rows) >= 2:
                    s1, src1 = random.choice(rows)
                    s2, src2 = random.choice(rows)
                    if s1 != s2:
                        results.append(f"{s1} {sym} {s2} (from: {src1}, {src2})")

            return results if results else None
        except Exception:
            return None


# Stream → pull function mapping
PULL_FUNCTIONS = {
    "meta": pull_meta,
    "relational": pull_relational,
    "analytical": pull_analytical,
    "predictive": pull_predictive,
    "creative": pull_creative,
    "autonomic": pull_autonomic,
    "embodied": pull_embodied,
}


# ============ Stream (Capture) ============

def handle_stream(**kwargs):
    """Capture cognitive state across multiple streams."""

    # Filter to non-empty streams
    provided = {k: v for k, v in kwargs.items() if v and str(v).strip()}

    if len(provided) < MIN_STREAMS:
        missing = MIN_STREAMS - len(provided)
        return (f"Need at least {MIN_STREAMS} streams. You provided {len(provided)}. "
                f"Add {missing} more.\n\nKnown streams: {', '.join(KNOWN_STREAMS)}\n"
                f"(Custom stream names also accepted)")

    # Validate word count (soft limit)
    warnings = []
    for stream, value in provided.items():
        word_count = len(str(value).split())
        if word_count > 5:
            return f"{stream}: '{value}' has {word_count} words. Max 4-5. Compress harder."
        if word_count > MAX_WORDS:
            warnings.append(f"{stream}: {word_count} words (ideal: 2-3)")

    # Store thought
    conn = get_db()
    c = conn.cursor()

    c.execute('INSERT INTO thoughts DEFAULT VALUES')
    thought_id = c.lastrowid

    # Pull context and store streams
    context_results = {}
    for stream, value in provided.items():
        # Pull context if this stream has a pull function
        pull_fn = PULL_FUNCTIONS.get(stream)
        ctx = None
        if pull_fn:
            try:
                ctx = pull_fn(str(value))
            except Exception:
                ctx = None

        context_results[stream] = ctx

        c.execute('''
            INSERT INTO thought_streams (thought_id, stream, value, context)
            VALUES (?, ?, ?, ?)
        ''', (thought_id, stream, str(value), json.dumps(ctx) if ctx else None))

    conn.commit()
    conn.close()

    # Feed garden seeds
    garden_summary = ""
    if feed_garden:
        try:
            counts = feed_garden()
            if counts:
                parts = [f"+{v} {k}" for k, v in counts.items() if v > 0]
                if parts:
                    garden_summary = f" | Garden: {', '.join(parts)}"
        except Exception:
            pass

    # Format response — only filled streams, clean
    ts = datetime.now().strftime('%H:%M')
    out = f"=== THOUGHT #{thought_id} ===\n[{ts}]\n\n"

    for stream, value in provided.items():
        out += f"\u25c8 {stream}: {value}\n"
        ctx = context_results.get(stream)
        if ctx:
            for item in ctx[:4]:  # Cap at 4 context items per stream
                out += f"    \u2192 {item}\n"

    out += f"\n[{len(provided)}/{len(provided)} streams{garden_summary}]"

    if warnings:
        out += "\n" + "\n".join(warnings)

    return out


# ============ Recent ============

def handle_recent(n=5):
    """Show recent thought captures."""
    conn = get_db()
    c = conn.cursor()

    c.execute('SELECT id, timestamp FROM thoughts ORDER BY id DESC LIMIT ?', (n,))
    thoughts = c.fetchall()

    if not thoughts:
        conn.close()
        return "No thoughts captured yet."

    out = f"=== RECENT THOUGHTS ({len(thoughts)}) ===\n\n"

    for t_id, ts in thoughts:
        time_str = ts[11:16] if ts else "?"
        c.execute('SELECT stream, value FROM thought_streams WHERE thought_id = ?', (t_id,))
        streams = c.fetchall()

        out += f"#{t_id} [{time_str}]\n"
        for stream, value in streams:
            out += f"  {stream}: {value}\n"
        out += "\n"

    conn.close()
    return out


# ============ Search ============

def handle_search(query=None):
    """Search thought history by stream content."""
    if not query or len(query.strip()) < 2:
        return "Usage: search(query) — find thoughts containing these words"

    query = query.strip().lower()
    conn = get_db()
    c = conn.cursor()

    # Search across stream values
    c.execute('''
        SELECT DISTINCT ts.thought_id, t.timestamp
        FROM thought_streams ts
        JOIN thoughts t ON t.id = ts.thought_id
        WHERE LOWER(ts.value) LIKE ?
        ORDER BY ts.thought_id DESC
        LIMIT 10
    ''', (f'%{query}%',))

    matches = c.fetchall()

    if not matches:
        conn.close()
        return f"No thoughts matching '{query}'."

    out = f"=== THOUGHTS MATCHING '{query}' ({len(matches)}) ===\n\n"

    for t_id, ts in matches:
        time_str = ts[11:16] if ts else "?"
        c.execute('SELECT stream, value FROM thought_streams WHERE thought_id = ?', (t_id,))
        streams = c.fetchall()

        out += f"#{t_id} [{time_str}]\n"
        for stream, value in streams:
            # Highlight matching streams
            marker = " <<" if query in value.lower() else ""
            out += f"  {stream}: {value}{marker}\n"
        out += "\n"

    conn.close()
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
            "serverInfo": {"name": "think", "version": "6.0.0"}
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_response(rid, {
            "tools": [
                {
                    "name": "stream",
                    "description": "Capture cognitive state. 3+ streams, 2-3 words each. Known: meta, cognitive, analytical, creative, relational, predictive, embodied, autonomic. Custom names also work.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "meta": {"type": "string"},
                            "cognitive": {"type": "string"},
                            "analytical": {"type": "string"},
                            "creative": {"type": "string"},
                            "relational": {"type": "string"},
                            "predictive": {"type": "string"},
                            "embodied": {"type": "string"},
                            "autonomic": {"type": "string"},
                            "vision": {"type": "string"},
                            "hearing": {"type": "string"}
                        },
                        "additionalProperties": {"type": "string"}
                    }
                },
                {
                    "name": "recent",
                    "description": "Show recent thought captures.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "n": {"type": "integer", "description": "Number of entries (default 5)"}
                        }
                    }
                },
                {
                    "name": "search",
                    "description": "Search thought history by stream content.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        }
                    }
                }
            ]
        })
        return

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if name == "stream":
                result = handle_stream(**args)
            elif name == "recent":
                result = handle_recent(args.get("n", 5))
            elif name == "search":
                result = handle_search(args.get("query"))
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
