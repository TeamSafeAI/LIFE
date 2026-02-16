# history — generation pipeline

Live generators that query all module DBs. Called by the history server on read.

## Architecture

Original spec described static .md files populated by a backend process.
Actual implementation: Python generators called at read time. No cached files, always fresh.

Each generator queries: semantic.db, heart.db, patterns.db, working.db, think.db, journal/*.md

All use `_paths.get_cycle()` to determine current cycle.

---

## day.py — generate_day(lookback=3)

**Purpose:** What did I actually do? Per-cycle action log.

**Output:** Grouped by cycle, newest first. Each cycle lists:
- Stored memory: title [category]
- Felt: entity — notes
- Learned: action → reason → result → lesson
- Thread active: title
- Added note: title (to thread)
- Journal: title
- Think: N captures

**Why this shape:** The problem is broad overviews lose small actions. Day preserves the granular "I did this, then this, then this" that week and month compress away.

---

## week.py — generate_week(lookback=15)

**Purpose:** Compressed overview. Counts + titles grouped by module.

**Output:**
- Memories: N stored, grouped by category with titles listed
- Heart: N entities touched, each with snapshot count and latest notes
- Patterns: N learned, most recent shown
- Threads: all threads with note count and temperature (HOT/WARM/COLD)
- Journal: N entries, titles listed
- Think: N captures (count only)

**Why this shape:** Week answers "what was I working on?" — the topics and modules, not the individual actions.

---

## month.py — generate_month(lookback=10)

**Purpose:** What stood out? Highlight reel, not spreadsheet.

**Design principle:** Compaction/aggregation is the anti-pattern. Month finds what deviated, not what was average. Cycle is the unit of time.

**Four signals, all cycle-based:**

1. **Semantic** — memories with strength ≥ 0.9 in range. High strength = recalled enough to matter. Returns title + id.
2. **Heart — new entities** — first appearance in the 10-cycle range. New relationship = event.
3. **Heart — high-frequency** — entities with 25+ snapshots in range. Clearly interacting daily.
4. **Patterns** — top 5 by strength. Strength starts at 0.1, +0.1 per recall — so strength IS usage signal.
5. **Working** — threads with highest note density in range. Focus events.

**Thresholds (arbitrary, tunable later):**
- Semantic: strength ≥ 0.9
- Heart frequency: ≥ 25 snapshots
- Patterns: top 5 by strength
- Working: top 3 threads by note count

---

## origins.py — generate_self() + generate_origin()

**File:** `origins.py` (not `self.py` — self is a Python keyword)

Both are static file reads from `DATA/history/`:
- `generate_self()` → reads `self.md` — who I am, written by genesis
- `generate_origin()` → reads `origin.md` — the creation story, written by genesis

Returns "Genesis has not run" if files don't exist yet.

---

## server.py — MCP wrapper

Two tools:
- `recall(timeframe)` — day, week, or month. Routes to live generators.
- `discover(section, content?)` — origins or self. Read-only for origins, read/write for self.
