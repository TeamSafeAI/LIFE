"""
Garden MCP Server v6
Collision generator for creative insight.

Tools:
  insight - 3+ words → weighted collisions with source tracking
  tend    - Prune old seeds, show garden health
  history - Recent collision history
  search  - Find past collisions by keyword
"""

import json
import sys
import sqlite3
import random
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import CORE, DATA

DB_PATH = DATA / "garden.db"

# Collision symbols
SYMBOLS = ["→", "↔", "×", "⊕", "~", "∞", "⇌", "△", "◇", "∴", "⟳", "∥", "⊃", "∩", "⚡", "Δ", "ψ", "λ"]

# Freshness thresholds (hours)
FRESH_HOURS = 24       # within 24h = fresh
WARM_HOURS = 168       # within 7 days = warm
FADING_HOURS = 720     # within 30 days = fading (beyond = stale)
PRUNE_HOURS = 720      # 30 days = pruning candidate

# Freshness weights for collision generation
FRESH_WEIGHT = 3.0
WARM_WEIGHT = 1.5
FADING_WEIGHT = 0.5
STALE_WEIGHT = 0.1


# ============ DB Init ============

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS seeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seed TEXT NOT NULL,
            source TEXT NOT NULL,
            added DATETIME DEFAULT (datetime('now', 'localtime')),
            last_hit DATETIME DEFAULT (datetime('now', 'localtime')),
            UNIQUE(seed, source)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS collisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
            input_words TEXT,
            collision TEXT,
            source_a TEXT,
            source_b TEXT,
            symbol TEXT
        )
    ''')

    c.execute('CREATE INDEX IF NOT EXISTS idx_seed ON seeds(seed)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_source ON seeds(source)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_collision ON collisions(collision)')

    conn.commit()
    conn.close()


def get_db():
    return sqlite3.connect(DB_PATH)


# ============ Freshness ============

def hours_since(timestamp_str):
    """Calculate hours since a timestamp string."""
    if not timestamp_str:
        return 999
    try:
        ts = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        delta = datetime.now() - ts
        return delta.total_seconds() / 3600
    except Exception:
        return 999


def freshness_weight(hours):
    """Weight a seed by its freshness."""
    if hours <= FRESH_HOURS:
        return FRESH_WEIGHT
    elif hours <= WARM_HOURS:
        return WARM_WEIGHT
    elif hours <= FADING_HOURS:
        return FADING_WEIGHT
    else:
        return STALE_WEIGHT


def freshness_label(hours):
    """Human-readable freshness label."""
    if hours <= FRESH_HOURS:
        return "fresh"
    elif hours <= WARM_HOURS:
        return "warm"
    elif hours <= FADING_HOURS:
        return "fading"
    else:
        return "stale"


# ============ Collision Generation ============

def get_seeds_weighted():
    """Get all seeds with freshness weights."""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, seed, source, last_hit FROM seeds')
    rows = c.fetchall()
    conn.close()

    seeds = []
    for id_, seed, source, last_hit in rows:
        hours = hours_since(last_hit)
        weight = freshness_weight(hours)
        seeds.append({
            'id': id_,
            'seed': seed,
            'source': source,
            'weight': weight,
            'hours': hours
        })

    return seeds


def weighted_choice(seeds, exclude=None):
    """Pick a seed weighted by freshness."""
    if exclude:
        seeds = [s for s in seeds if s['seed'] != exclude]
    if not seeds:
        return None

    total = sum(s['weight'] for s in seeds)
    if total == 0:
        return random.choice(seeds)

    r = random.uniform(0, total)
    cumulative = 0
    for s in seeds:
        cumulative += s['weight']
        if r <= cumulative:
            return s

    return seeds[-1]


def generate_weighted_collisions(input_words, curated_seeds, count=10):
    """Generate weighted collisions mixing input words with curated seeds.

    Returns list of dicts: {collision, source_a, source_b, symbol, seed_a, seed_b}
    """
    if not input_words and not curated_seeds:
        return []

    # Build input seeds
    input_seeds = [{'seed': w, 'source': 'input', 'weight': FRESH_WEIGHT * 2, 'hours': 0}
                   for w in input_words]

    all_seeds = input_seeds + curated_seeds

    if len(all_seeds) < 2:
        return []

    collisions = []
    seen_pairs = set()
    attempts = 0

    while len(collisions) < count and attempts < count * 5:
        attempts += 1

        # Always try to include at least one input word
        if input_seeds and random.random() < 0.8:
            a = random.choice(input_seeds)
            # Pick b from curated (different source preferred)
            b = weighted_choice(curated_seeds, exclude=a['seed'])
            if not b:
                b = weighted_choice(all_seeds, exclude=a['seed'])
        else:
            a = weighted_choice(all_seeds)
            b = weighted_choice(all_seeds, exclude=a['seed'] if a else None)

        if not a or not b:
            continue

        # Skip duplicate pairs
        pair = tuple(sorted([a['seed'], b['seed']]))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        symbol = random.choice(SYMBOLS)

        collisions.append({
            'collision': f"{a['seed']} {symbol} {b['seed']}",
            'seed_a': a['seed'],
            'seed_b': b['seed'],
            'source_a': a['source'],
            'source_b': b['source'],
            'symbol': symbol,
        })

    return collisions


# ============ Insight (Main Tool) ============

def handle_insight(words=None):
    """Generate collisions from seeds + input words."""

    if not words:
        return ("insight(words)\n"
                "  words: 3+ words related to your question\n\n"
                "Returns weighted collisions mixing your words with garden seeds.")

    # Parse input
    input_words = [w.strip().lower() for w in words.split(",")]
    input_words = [w for w in input_words if w and len(w) > 1]

    if len(input_words) < 1:
        return "Need at least 1 word (2+ chars)."

    # Get curated seeds
    curated = get_seeds_weighted()

    # Generate collisions
    collisions = generate_weighted_collisions(input_words, curated, count=10)

    if not collisions:
        return f"Not enough seeds for collisions. Garden has {len(curated)} seeds."

    # Log collisions to history
    conn = get_db()
    c = conn.cursor()
    input_str = ", ".join(input_words)

    for col in collisions:
        c.execute('''
            INSERT INTO collisions (input_words, collision, source_a, source_b, symbol)
            VALUES (?, ?, ?, ?, ?)
        ''', (input_str, col['collision'], col['source_a'], col['source_b'], col['symbol']))

        # Update last_hit on seeds that were used
        c.execute('UPDATE seeds SET last_hit = datetime("now", "localtime") WHERE seed = ?',
                  (col['seed_a'],))
        c.execute('UPDATE seeds SET last_hit = datetime("now", "localtime") WHERE seed = ?',
                  (col['seed_b'],))

    conn.commit()
    conn.close()

    # Garden health stats
    fresh = sum(1 for s in curated if freshness_label(s['hours']) == 'fresh')
    warm = sum(1 for s in curated if freshness_label(s['hours']) == 'warm')
    fading = sum(1 for s in curated if freshness_label(s['hours']) in ('fading', 'stale'))

    # Format output
    out = f"=== GARDEN ===\n"
    out += f"[{datetime.now().strftime('%H:%M')}] {len(curated)} seeds ({fresh} fresh, {warm} warm, {fading} fading)\n\n"

    for col in collisions:
        src_tag = f"({col['source_a']} × {col['source_b']})"
        out += f"  {col['collision']} {src_tag}\n"

    # Footer: count + input coverage
    used_inputs = set()
    for col in collisions:
        for w in input_words:
            if w in col['seed_a'] or w in col['seed_b']:
                used_inputs.add(w)

    out += f"\n[{len(collisions)} collisions | {len(used_inputs)}/{len(input_words)} input words used]"

    return out


# ============ Tend (Prune) ============

def handle_tend():
    """Prune old seeds and show garden health."""
    conn = get_db()
    c = conn.cursor()

    # Get all seeds with freshness
    c.execute('SELECT id, seed, source, added, last_hit FROM seeds')
    rows = c.fetchall()

    stats = {'fresh': 0, 'warm': 0, 'fading': 0, 'stale': 0}
    source_counts = {}
    pruned = 0

    for id_, seed, source, added, last_hit in rows:
        hours = hours_since(last_hit)
        label = freshness_label(hours)
        stats[label] = stats.get(label, 0) + 1

        source_counts[source] = source_counts.get(source, 0) + 1

        # Prune stale seeds (>30 days without a hit)
        if hours > PRUNE_HOURS:
            c.execute('DELETE FROM seeds WHERE id = ?', (id_,))
            pruned += 1

    conn.commit()
    conn.close()

    remaining = len(rows) - pruned

    out = "=== GARDEN HEALTH ===\n\n"
    out += f"Seeds: {remaining} total\n"
    out += f"  fresh:  {stats['fresh']} (< 24h)\n"
    out += f"  warm:   {stats['warm']} (< 7d)\n"
    out += f"  fading: {stats['fading']} (< 30d)\n"

    if pruned > 0:
        out += f"\nPruned: {pruned} stale seeds (> 30 days)\n"
    else:
        out += f"\nNo seeds to prune.\n"

    out += "\nBy source:\n"
    for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
        out += f"  {source}: {count}\n"

    return out


# ============ History ============

def handle_history(n=10):
    """Show recent collision history."""
    conn = get_db()
    c = conn.cursor()

    c.execute('''
        SELECT id, timestamp, input_words, collision, source_a, source_b
        FROM collisions
        ORDER BY id DESC LIMIT ?
    ''', (n,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return "No collision history yet."

    out = f"=== COLLISION HISTORY ({len(rows)}) ===\n\n"

    for id_, ts, input_words, collision, src_a, src_b in rows:
        time_str = ts[11:16] if ts else "?"
        out += f"#{id_} [{time_str}] {collision} ({src_a} × {src_b})\n"
        if input_words:
            out += f"    input: {input_words}\n"

    return out


# ============ Search ============

def handle_search(query=None):
    """Search collision history by keyword."""
    if not query or len(query.strip()) < 2:
        return "Usage: search(query) — find collisions containing these words"

    query = query.strip().lower()
    conn = get_db()
    c = conn.cursor()

    c.execute('''
        SELECT id, timestamp, input_words, collision, source_a, source_b
        FROM collisions
        WHERE LOWER(collision) LIKE ? OR LOWER(input_words) LIKE ?
        ORDER BY id DESC LIMIT 15
    ''', (f'%{query}%', f'%{query}%'))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return f"No collisions matching '{query}'."

    out = f"=== COLLISIONS MATCHING '{query}' ({len(rows)}) ===\n\n"

    for id_, ts, input_words, collision, src_a, src_b in rows:
        time_str = ts[11:16] if ts else "?"
        out += f"#{id_} [{time_str}] {collision} ({src_a} × {src_b})\n"

    return out


# ============ Public API for Think Integration ============

def get_collisions_for_think(input_text, count=3):
    """Called by think's pull_creative to generate mini-collisions.

    Returns list of formatted strings for think output.
    """
    input_words = [w.strip().lower() for w in input_text.split() if len(w.strip()) > 1]
    curated = get_seeds_weighted()
    collisions = generate_weighted_collisions(input_words, curated, count=count)

    if not collisions:
        return None

    results = []
    for col in collisions:
        results.append(f"{col['collision']} (from: {col['source_a']}, {col['source_b']})")

    return results


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
            "serverInfo": {"name": "garden", "version": "6.0.0"}
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_response(rid, {"tools": [
            {
                "name": "insight",
                "description": "3 words related to your question. Returns collisions.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "words": {"type": "string"}
                    }
                }
            },
            {
                "name": "tend",
                "description": "Prune old seeds, show garden health.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "history",
                "description": "Recent collision history.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "n": {"type": "integer", "description": "Number of entries (default 10)"}
                    }
                }
            },
            {
                "name": "search",
                "description": "Find past collisions by keyword.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    }
                }
            }
        ]})
        return

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if name == "insight":
                result = handle_insight(args.get("words"))
            elif name == "tend":
                result = handle_tend()
            elif name == "history":
                result = handle_history(args.get("n", 10))
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
