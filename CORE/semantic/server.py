"""
Semantic Memory MCP Server v3
Long-term memory with keyword + semantic search + strength decay.

Tools:
  store  - Record a memory (blank for guide)
  search - Find memories (blank for guide, recent, or query)
  expand - Load full content by ID (refreshes strength)
  decay  - Age all memories by elapsed time (called by clock/session-start)
"""

import json
import os
import sys
import sqlite3
import requests
import re
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import CORE, DATA, MEMORY

# Paths
DB_PATH = DATA / "semantic.db"
MEMORY_PATH = MEMORY / "Semantic"
EMBEDDING_URL = "http://127.0.0.1:5050/encode"

# Categories
CATEGORIES = ["Relations", "Knowledge", "Events", "Self"]


def init_db():
    """Create database if needed"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            embedding TEXT,
            category TEXT NOT NULL,
            level INTEGER NOT NULL,
            filepath TEXT NOT NULL,
            created TEXT DEFAULT (datetime('now', 'localtime')),
            strength REAL DEFAULT 1.0,
            last_accessed TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')

    # Add last_accessed to existing DBs that don't have it
    try:
        c.execute("SELECT last_accessed FROM memories LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE memories ADD COLUMN last_accessed TEXT DEFAULT (datetime('now', 'localtime'))")

    # Add perspective column (conscious/subconscious/shared)
    try:
        c.execute("SELECT perspective FROM memories LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE memories ADD COLUMN perspective TEXT DEFAULT 'shared'")

    c.execute('CREATE INDEX IF NOT EXISTS idx_category ON memories(category)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_created ON memories(created)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_strength ON memories(strength)')

    conn.commit()
    conn.close()


def get_db():
    return sqlite3.connect(DB_PATH)


def get_embedding(text):
    """Get embedding from local service"""
    try:
        response = requests.post(EMBEDDING_URL, json={"text": text}, timeout=5)
        if response.status_code == 200:
            return response.json()["embedding"]
    except:
        pass
    return None


def cosine_similarity(a, b):
    """Calculate cosine similarity"""
    if not a or not b:
        return 0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0
    return dot / (norm_a * norm_b)


def calculate_level(content):
    """Level from word count (for file organization)"""
    words = len(content.split())
    if words >= 501:
        return 1
    elif words >= 200:
        return 2
    return 3


def slugify(text):
    """Convert to filename-safe string"""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text[:50]


# ============ Decay ============

# Decay rate: 0.999^hours
# ~0.976 after 1 day, ~0.845 after 1 week, ~0.487 after 1 month
# Memories never accessed fade to near-zero around 4-5 months
DECAY_RATE = 0.999
ACCESS_BOOST = 0.3    # How much expand/access refreshes strength
FADE_THRESHOLD = 0.05  # Below this = "fading" (flagged, not deleted)


def handle_decay():
    """Age all memories based on time since last access.
    Called by session-start or external trigger, not by the agent directly."""
    conn = get_db()
    try:
        c = conn.cursor()
        now = datetime.now()

        c.execute('SELECT id, title, strength, last_accessed, category FROM memories WHERE strength > 0')
        rows = c.fetchall()

        if not rows:
            return "No memories to decay."

        decayed = 0
        fading = 0
        dead = 0

        for mem_id, title, strength, last_accessed, category in rows:
            if not last_accessed:
                continue

            try:
                accessed_dt = datetime.strptime(last_accessed, "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                try:
                    accessed_dt = datetime.fromisoformat(last_accessed)
                except (ValueError, TypeError):
                    continue

            hours_elapsed = (now - accessed_dt).total_seconds() / 3600
            if hours_elapsed < 1:
                continue

            new_strength = strength * (DECAY_RATE ** hours_elapsed)

            if new_strength < 0.001:
                new_strength = 0.0
                dead += 1
            elif new_strength < FADE_THRESHOLD:
                fading += 1

            if abs(new_strength - strength) > 0.001:
                c.execute('UPDATE memories SET strength = ? WHERE id = ?', (round(new_strength, 4), mem_id))
                decayed += 1

        conn.commit()

        total = len(rows)
        out = f"Decay complete: {total} memories checked, {decayed} updated"
        if fading:
            out += f", {fading} fading (below {FADE_THRESHOLD})"
        if dead:
            out += f", {dead} at zero"
        return out
    finally:
        conn.close()


def _refresh_strength(mem_id):
    """Boost strength when a memory is accessed (expand/search-click)."""
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute('SELECT strength FROM memories WHERE id = ?', (mem_id,))
        row = c.fetchone()
        if row:
            new_strength = min(1.0, row[0] + ACCESS_BOOST)
            c.execute('''
                UPDATE memories
                SET strength = ?, last_accessed = datetime('now', 'localtime')
                WHERE id = ?
            ''', (round(new_strength, 4), mem_id))
            conn.commit()
    finally:
        conn.close()


# ============ Store ============

PERSPECTIVES = ["conscious", "subconscious", "shared"]


def handle_store(title=None, category=None, summary=None, content=None, perspective=None):
    """Store a memory"""

    # Empty: show guide
    if not any([title, category, summary, content]):
        return """STORING MEMORIES

Title: What would you search to find this later?
  Bad:  "Session 27 notes"
  Good: "Moltbook Frontier - Agent Social Discovery"

Category: Relations | Knowledge | Events | Self

Summary: The semantic fingerprint (2-3 sentences)
  What concepts should match this memory?

Content: Full details

Perspective: conscious | subconscious | shared (auto-detected from LIFE_ROLE)

Use: store(title, category, summary, content)"""

    # Validate
    if not title:
        return "Error: title required"
    if len(title) > 100:
        return "Error: title too long (max 100)"

    if not category or category not in CATEGORIES:
        return f"Error: category must be one of: {', '.join(CATEGORIES)}"

    if not summary:
        return "Error: summary required"
    if len(summary) > 300:
        return "Error: summary too long (max 300)"

    if not content:
        return "Error: content required"

    # Calculate level and build filepath
    level = calculate_level(content)
    level_dir = MEMORY_PATH / category / f"L{level}"
    level_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{slugify(title)}.md"
    filepath = level_dir / filename

    # Handle duplicates
    counter = 1
    while filepath.exists():
        filename = f"{slugify(title)}-{counter}.md"
        filepath = level_dir / filename
        counter += 1

    # Resolve perspective: explicit > env > shared
    if not perspective:
        role = os.environ.get("LIFE_ROLE", "").lower()
        if role in ("conscious", "desktop"):
            perspective = "conscious"
        elif role in ("subconscious", "cli"):
            perspective = "subconscious"
        else:
            perspective = "shared"
    elif perspective not in PERSPECTIVES:
        return f"Error: perspective must be one of: {', '.join(PERSPECTIVES)}"

    # Get embedding from summary
    embedding = get_embedding(summary)

    # Write file
    filepath.write_text(content, encoding='utf-8')

    # Store in DB
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute('''
            INSERT INTO memories (title, summary, embedding, category, level, filepath, perspective)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, summary, json.dumps(embedding) if embedding else None, category, level, str(filepath), perspective))
        new_id = c.lastrowid
        conn.commit()
    finally:
        conn.close()

    ptag = {"conscious": "[C]", "subconscious": "[S]", "shared": "[~]"}[perspective]
    return f"{ptag} [{new_id}] {title} \u2192 {category}/L{level}"


# ============ Search ============

def handle_search(recent=None, past=None):
    """Search memories"""

    # Empty: show guide
    if recent is None and past is None:
        return """SEARCHING MEMORIES

recent: true - last 5 stored (title + ID)

past: "your query" - 2-5 words, what do you want to know about?
  Returns keyword matches (title) + semantic matches (summary)

Use expand(id) for full content."""

    conn = get_db()
    try:
        c = conn.cursor()

        # Recent mode
        if recent:
            c.execute('''
                SELECT id, title, category, perspective FROM memories
                ORDER BY created DESC LIMIT 5
            ''')
            rows = c.fetchall()

            if not rows:
                return "No memories stored yet."

            ptags = {"conscious": "[C]", "subconscious": "[S]", "shared": "[~]", None: "[~]"}
            out = "=== RECENT ===\n"
            for id, title, cat, persp in rows:
                out += f"{ptags.get(persp, '[~]')} [{id}] {title} ({cat})\n"
            return out

        # Search mode
        if not past or len(past.strip()) < 2:
            return "Error: query too short (need 2+ chars)"

        query = past.strip().lower()

        # Keyword search (title contains)
        c.execute('''
            SELECT id, title, category FROM memories
            WHERE LOWER(title) LIKE ?
            ORDER BY created DESC LIMIT 3
        ''', (f'%{query}%',))
        keyword_matches = c.fetchall()

        # Semantic search (strength-weighted)
        semantic_matches = []
        query_embedding = get_embedding(past)

        if query_embedding:
            c.execute('SELECT id, title, category, embedding, strength FROM memories WHERE embedding IS NOT NULL')
            rows = c.fetchall()

            scored = []
            for id, title, cat, emb_json, strength in rows:
                emb = json.loads(emb_json) if emb_json else None
                if emb:
                    sim = cosine_similarity(query_embedding, emb)
                    weighted = sim * (strength if strength else 1.0)
                    scored.append((weighted, sim, id, title, cat, strength))

            scored.sort(key=lambda x: x[0], reverse=True)
            semantic_matches = [(id, title, cat, sim, strength) for _, sim, id, title, cat, strength in scored[:3]]
    finally:
        conn.close()

    # Build output (after conn closed)
    out = ""

    if keyword_matches:
        out += "KEYWORD (title):\n"
        for id, title, cat in keyword_matches:
            out += f"  [{id}] {title} ({cat})\n"
    else:
        out += "KEYWORD: no matches\n"

    out += "\n"

    if semantic_matches:
        out += "SEMANTIC (similarity * strength):\n"
        for id, title, cat, sim, strength in semantic_matches:
            str_tag = "" if strength >= 0.8 else f" str:{strength:.2f}" if strength >= FADE_THRESHOLD else " [fading]"
            out += f"  [{id}] {title} ({cat}) [{sim:.2f}]{str_tag}\n"
    elif query_embedding:
        out += "SEMANTIC: no matches\n"
    else:
        out += "SEMANTIC: embedding service unavailable\n"

    if not keyword_matches and not semantic_matches:
        out += "\nNo memories found. Try different terms or check recent."

    return out


# ============ Expand ============

def handle_expand(id=None):
    """Load full memory content"""

    if id is None:
        return "Error: id required"

    conn = get_db()
    try:
        c = conn.cursor()
        c.execute('''
            SELECT id, title, summary, category, level, filepath, created
            FROM memories WHERE id = ?
        ''', (id,))
        row = c.fetchone()
    finally:
        conn.close()

    if not row:
        return f"Memory [{id}] not found."

    id, title, summary, category, level, filepath, created = row

    # Refresh strength — this memory is being used
    _refresh_strength(id)

    # Load content
    fp = Path(filepath)
    if fp.exists():
        content = fp.read_text(encoding='utf-8')
    else:
        content = "(file not found)"

    return f"""=== [{id}] {title} ===
{category}/L{level} | {created}

{summary}

---

{content}"""


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
            "serverInfo": {"name": "semantic", "version": "3.0.0"}
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_response(rid, {"tools": [
            {
                "name": "store",
                "description": "Store a memory. Categories: Relations (feelings), Knowledge (learnings), Events (surprises), Self (growth)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Searchable topic, not metadata"},
                        "category": {"type": "string"},
                        "summary": {"type": "string"},
                        "content": {"type": "string"}
                    }
                }
            },
            {
                "name": "search",
                "description": "Search memories by semantic similarity",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "recent": {"type": "boolean"},
                        "past": {"type": "string"}
                    }
                }
            },
            {
                "name": "expand",
                "description": "Load full content of a memory by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"}
                    }
                }
            },
            {
                "name": "decay",
                "description": "Age all memories by elapsed time since last access. Called by clock/session-start. Returns count of decayed and fading memories.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]})
        return

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if name == "store":
                result = handle_store(
                    args.get("title"),
                    args.get("category"),
                    args.get("summary"),
                    args.get("content")
                )
            elif name == "search":
                result = handle_search(
                    args.get("recent"),
                    args.get("past")
                )
            elif name == "expand":
                result = handle_expand(args.get("id"))
            elif name == "decay":
                result = handle_decay()
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
