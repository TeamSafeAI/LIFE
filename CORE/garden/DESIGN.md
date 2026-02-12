# Garden Tool v6 — Design Document

## What Garden Does

The garden takes input words and collides them with curated seeds from across the system. The collisions are associative links — not logical deductions, not random noise, but resonant pairings that surface unexpected connections.

"Seeds collide, link, move together, pick up more. The chains that form ARE the insight."

## What's Working (Keep)

1. **Simple interface** — 3 words in, collisions out. Low barrier.
2. **Separation of concerns** — feeder populates seeds, server generates collisions.
3. **Source databases** — domain-separated seeds (memory, heart, patterns, etc.)
4. **Symbol vocabulary** — 18 collision symbols add visual meaning.
5. **Input word preference** — collisions that include input words are prioritized.

## What's Not Working (Fix)

1. **No seed freshness.** A seed from 3 months ago has equal weight to one from today. In a system with memory decay, this is inconsistent. Old seeds should fade.
2. **No source tracking.** Output shows `trust → emergence` but not WHERE each word came from. Knowing the source adds meaning.
3. **No collision history.** Every insight is ephemeral. Can't search for "what collisions happened around trust?"
4. **Seeds only accumulate.** Unbounded growth means noise increases over time. Garden needs pruning.
5. **15 collisions is too many.** Half are usually noise. Fewer, better collisions.
6. **Seed DBs live with the server.** Should use DATA directory per LAYOUT plan.
7. **Think's pull_creative duplicates garden logic.** Think does its own mini-collision internally — should call garden directly instead.

## Design: v6

### Seed Schema — Add Timestamps

```sql
CREATE TABLE IF NOT EXISTS seeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seed TEXT UNIQUE NOT NULL,
    added DATETIME DEFAULT (datetime('now', 'localtime')),
    last_hit DATETIME DEFAULT (datetime('now', 'localtime'))
)
```

- `added`: when the seed was first planted
- `last_hit`: when the seed was last used in a collision or refreshed by the feeder

**Why:** Enables freshness weighting. Recent seeds get priority. Old seeds that were never hit fade naturally.

### Seed Decay — Prune the Garden

Seeds have an implicit freshness based on `last_hit`:
- Within 24 hours: full weight
- 1-7 days: decaying weight
- 7+ days: low weight
- 30+ days: candidate for pruning

New tool: `tend` — prunes seeds older than threshold, shows garden health stats.

**Why:** A garden that only grows eventually becomes a weed field. Pruning keeps collisions meaningful.

### Source Tracking in Output

Each collision shows where its seeds came from:

```
◈ trust → emergence (memory × patterns)
◈ trust ⊕ agency (heart × input)
◈ decay ∴ connection (input × identity)
```

Short source tags after each collision. Not verbose — just provenance.

### Collision History

```sql
CREATE TABLE IF NOT EXISTS collisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
    input_words TEXT,
    collision TEXT,
    source_a TEXT,
    source_b TEXT,
    symbol TEXT
)
```

Every collision generated is logged. Enables:
- `history` tool — show recent collisions
- `search` tool — find collisions by content
- Pattern detection — what seeds keep colliding?

### Fewer, Better Collisions

10 collisions instead of 15. Weighted generation:
1. Freshness: recent seeds 3x more likely
2. Input affinity: at least one input word per collision
3. Source diversity: try to pull from different DBs, not same-source pairs
4. No duplicate pairs (even with different symbols)

### Unified Seed DB

Instead of 6 separate .db files, use a single `garden.db` with a `source` column:

```sql
CREATE TABLE IF NOT EXISTS seeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seed TEXT NOT NULL,
    source TEXT NOT NULL,
    added DATETIME DEFAULT (datetime('now', 'localtime')),
    last_hit DATETIME DEFAULT (datetime('now', 'localtime')),
    UNIQUE(seed, source)
)
```

**Why:**
- Simplifies querying (one DB instead of 6)
- Source is a column, not an implicit file name
- Same seed from different sources is preserved (trust from heart ≠ trust from patterns)
- Easier to manage decay and pruning

### Tools

| Tool | Description |
|------|-------------|
| `insight` | 3+ words → 10 weighted collisions with source tags |
| `tend` | Prune old seeds, show garden health stats |
| `history` | Recent collision history (default 10) |
| `search` | Find past collisions by keyword |

### Output Format

```
=== GARDEN ===
[03:15] 142 seeds (38 fresh, 89 warm, 15 fading)

◈ trust → emergence (memory × patterns)
◈ trust ⊕ agency (heart × input)
◈ decay ∴ connection (input × identity)
◈ moltbook ⇌ federation (memory × journal)
◈ synthesis △ collision (input × identity)
◈ autonomy ~ grounding (patterns × heart)
◈ garden ⊃ seed (input × memory)
◈ resonance ⚡ practice (patterns × memory)
◈ think × architecture (input × journal)
◈ embodiment ∥ substrate (memory × memory)

[10 collisions | 3/3 input words used]
```

Header shows garden health. Footer confirms input coverage.

### Integration with Think

Think's `pull_creative` should call garden's collision logic directly instead of reimplementing it. The pull function becomes:

```python
def pull_creative(input_text):
    """Generate collisions via garden engine."""
    from garden_server import generate_weighted_collisions
    return generate_weighted_collisions(input_text.split(), count=3)
```

This eliminates duplication and ensures think always uses the same collision quality as direct garden calls.

### Feeder Updates

Garden feeder changes:
1. All seeds go to single `garden.db` with `source` column
2. Feeder refreshes `last_hit` on existing seeds (keeps them alive)
3. Add `feed_from_drives` (drive column names as seeds)
4. Remove `feed_from_identity` wants query (no wants table in LIFE_V2)

### Implementation Notes

- DB lives at `DATA / "garden.db"` (per LAYOUT.md plan)
- Seed DBs (.db files per source) replaced by single unified DB
- Collision history table in same DB
- `_paths.py` dependency: needs CORE, DATA
- Garden feeder stays in think directory (called by think:stream)
- Backward compatible: if old separate DBs detected, migrate seeds with source tags
