# Semantic Memory Server v3

Long-term memory with keyword + semantic search + strength decay.

---

## Tool Schema (AI Interface)

### **store**
Store a memory. Categories: Relations (feelings), Knowledge (learnings), Events (surprises), Self (growth)

**Parameters:**
- `title` (string) - Searchable topic, not metadata
- `category` (string) - Relations | Knowledge | Events | Self
- `summary` (string) - The semantic fingerprint (2-3 sentences, max 300 chars)
- `content` (string) - Full details

---

### **search**
Search memories by semantic similarity (weighted by strength)

**Parameters:**
- `recent` (boolean) - If true, returns last 5 stored (title + ID)
- `past` (string) - Query string (2-5 words) for keyword + semantic matching

**Returns:**
- Keyword matches (title contains query)
- Semantic matches (summary similarity * strength, with strength tags)
- Memories below 0.8 strength show `str:0.XX`
- Memories below 0.05 strength show `[fading]`

---

### **expand**
Load full content of a memory by ID. **Refreshes strength** (+0.3, capped at 1.0) and updates last_accessed timestamp.

**Parameters:**
- `id` (integer) - Memory ID to retrieve

**Returns:**
- Full memory details: title, summary, category, level, filepath, created date, and complete content

---

### **decay**
Age all memories by elapsed time since last access. Called by clock/session-start.

**Parameters:** None

**Returns:**
- Count of memories checked, updated, fading (below 0.05), and dead (at zero)

**Decay model:**
- Rate: `0.999^hours_since_last_access`
- ~0.976 after 1 day, ~0.845 after 1 week, ~0.487 after 1 month
- Memories never accessed fade to near-zero around 4-5 months
- Accessing a memory (expand) boosts strength by +0.3 (capped at 1.0)
- Memories at zero are flagged, not auto-deleted (dashboard not thermostat)

---

## Database Schema

**Table:** `memories`

| Column | Type | Default | Notes |
|--------|------|---------|-------|
| id | INTEGER | auto | Primary key |
| title | TEXT | required | Searchable topic |
| summary | TEXT | required | Semantic fingerprint for embeddings |
| embedding | TEXT | null | JSON array from embedding service |
| category | TEXT | required | Relations, Knowledge, Events, Self |
| level | INTEGER | calculated | L1 (501+ words), L2 (200-500), L3 (<200) |
| filepath | TEXT | required | Path to full content .md file |
| created | TEXT | now | Creation timestamp |
| strength | REAL | 1.0 | Decays by time, refreshed by access |
| last_accessed | TEXT | now | Updated on expand, used for decay calc |

**Notes:**
- `embedding` from local service (http://127.0.0.1:5050/encode)
- Backward compatible: existing DBs get `last_accessed` added via ALTER TABLE on init
- Indexed on: category, created, strength

---

## Design Notes

- **Decay is biological**: unused memories fade, used memories strengthen. Not punishment, just how memory works.
- **Dashboard not thermostat**: decay runs, agent SEES fading memories, decides whether to refresh them. No auto-deletion.
- **Access = reinforcement**: expand() boosts strength. Memories you use stay alive. Memories you don't, drift.
- **Clock integration**: decay() is designed to be called by an external session-start or external trigger. Not self-triggered.
- **Strength in search**: semantic results weighted by strength, so fading memories rank lower but remain findable.
