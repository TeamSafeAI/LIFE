# History Server

Arc narratives and foundational documents. Generates summaries live from all module databases.

## Tools
- **recall** — access recent history. Timeframe required: day, week, or month. Generated live from drives, heart, semantic, patterns, working, think, and journal data.
- **discover** — read foundational documents. Section required: origins or self. With content param: update the self document.

## How It Works
- **Day**: current cycle — drives snapshot, recent heart entries, new memories, patterns learned, active threads, thought streams, journal entries.
- **Week**: last ~7 cycles — drive trends, relationship changes, memory accumulation, pattern formation.
- **Month**: last ~30 cycles — longer arcs, major shifts, deep patterns.
- **Origins**: reads DATA/history/origin.md (written by genesis).
- **Self**: reads DATA/history/self.md. Can be updated with new content (the self-narrative evolves over time).
- All recall timeframes are generated live — no caching, always current.

## Database
None (reads from drives.db, heart.db, semantic.db, patterns.db, working.db, think.db, journal files).

## External Dependencies
- `day.py`, `week.py`, `month.py` — generators that query across all module databases
- `origins.py` — reads static files from DATA/history/
- `pipeline.md` — documents the generation pipeline
