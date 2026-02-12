# Garden Server v6

Collision generator for creative insight with seed freshness, source tracking, and collision history.

Seeds populated by think:stream via garden_feeder.py. Reads from unified `garden.db`.

---

## Tool Schema (AI Interface)

### **insight**
3+ words related to your question. Returns weighted collisions with source tags.

**Parameters:**
- `words` (string) - Comma-separated words (at least 1 word, 2+ chars each)

**Returns:**
- 10 weighted collisions mixing input words with curated seeds
- Each collision tagged with source (memory, heart, patterns, etc.)
- Garden health stats in header (fresh/warm/fading counts)
- Uses symbols: → ↔ × ⊕ ~ ∞ ⇌ △ ◇ ∴ ⟳ ∥ ⊃ ∩ ⚡ Δ ψ λ

**Example:**
```
=== GARDEN ===
[03:15] 142 seeds (38 fresh, 89 warm, 15 fading)

  trust → emergence (memory × patterns)
  trust ⊕ agency (heart × input)
  decay ∴ connection (input × drives)
  moltbook ⇌ federation (memory × working)
  synthesis △ collision (input × drives)
  autonomy ~ grounding (patterns × heart)
  garden ⊃ seed (input × memory)
  resonance ⚡ practice (patterns × memory)
  think × architecture (input × working)
  embodiment ∥ substrate (memory × memory)

[10 collisions | 3/3 input words used]
```

**Freshness weighting:**
- Fresh seeds (< 24h) are 3x more likely to appear
- Warm seeds (< 7 days) are 1.5x more likely
- Fading seeds (< 30 days) are 0.5x
- Stale seeds (> 30 days) are 0.1x (and pruned by tend)

---

### **tend**
Prune old seeds, show garden health.

**Parameters:** None

**Returns:**
- Seed counts by freshness (fresh/warm/fading)
- Count of pruned stale seeds (> 30 days without a hit)
- Breakdown by source

**Example:**
```
=== GARDEN HEALTH ===

Seeds: 142 total
  fresh:  38 (< 24h)
  warm:   89 (< 7d)
  fading: 15 (< 30d)

No seeds to prune.

By source:
  memory: 45
  patterns: 32
  heart: 28
  working: 20
  journal: 12
  drives: 5
```

---

### **history**
Recent collision history.

**Parameters:**
- `n` (integer) - Number of entries (default 10)

**Returns:**
- Recent collisions with timestamps, sources, and input words

---

### **search**
Find past collisions by keyword.

**Parameters:**
- `query` (string) - Words to search for in collision text or input words

**Returns:**
- Matching collisions with timestamps and sources

---

## Database Schema

**Single unified DB:** `DATA/garden.db`

**Table: `seeds`**

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key |
| seed | TEXT | The seed word/phrase |
| source | TEXT | Where it came from (memory, heart, patterns, working, journal, drives) |
| added | DATETIME | When first planted |
| last_hit | DATETIME | When last used in collision or refreshed by feeder |

UNIQUE constraint on (seed, source) — same word from different sources preserved.

**Table: `collisions`**

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key |
| timestamp | DATETIME | When generated |
| input_words | TEXT | Comma-separated input |
| collision | TEXT | Full collision string (e.g., "trust → emergence") |
| source_a | TEXT | Source of first seed |
| source_b | TEXT | Source of second seed |
| symbol | TEXT | The collision symbol used |

---

## Seed Sources

| Source Tag | Where It Comes From | Feeder Function |
|-----------|--------------------|-----------------|
| memory | Semantic memory titles | feed_from_semantic |
| heart | Entity names from heart DB | feed_from_heart |
| patterns | Action/reason/result from patterns | feed_from_patterns |
| working | Active thread titles | feed_from_working |
| journal | Journal file names | feed_from_journal |
| drives | Drive column names (connection, synthesis, etc.) | feed_from_drives |
| input | User's input words (added at collision time, not stored) | — |

---

## Design Notes

- **Unified DB** replaces 6 separate seed databases. Source is a column, not a file.
- **Freshness weighting** means recent seeds dominate collisions. Old seeds fade naturally.
- **Collision history** makes insights searchable and trackable over time.
- **Source tags** in output show provenance — knowing WHERE a collision came from adds meaning.
- **Tend tool** prunes stale seeds (>30 days), keeping the garden productive.
- **Think integration** — think's `pull_creative` delegates to garden's collision engine via `get_collisions_for_think()`.
- **Seeds keep moving** — using a seed in a collision refreshes its `last_hit`, keeping it alive.
