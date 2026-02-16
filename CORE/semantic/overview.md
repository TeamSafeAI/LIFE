# Semantic Memory Server

Long-term memory with embeddings. DB is the index, .md files are the content.

## Tools
- **store** — save a memory. Title + category + summary + content required. Summary gets embedded (75 word cap). Content saved as .md file in MEMORY/{category}/L{level}/. Level from word count (L1≤250, L2≤500, L3 500+). Reports similar memories on store.
- **search** — no params: last 10 by recency. With query: two-pass (keyword LIKE on title + semantic cosine similarity). Deduplicates. Boosts all hits +0.1 strength.
- **expand** — load full .md content by ID. Boosts strength +0.5 (deep recall reinforcement).

## How It Works
- DB row = index (title, summary, embedding, category, level, strength, cycle). File = full content.
- Embeddings via external service (localhost:5050, all-MiniLM-L6-v2, 384-dim). Gracefully optional — if service is down, store still works (embedding=NULL), search falls back to keyword-only.
- Strength: starts 1.0, search boost +0.1, expand boost +0.5, capped at 1.0. Higher strength = more important/recalled.
- Similar memory detection on store: cosine similarity ≥0.75 against existing embeddings.
- File stored at MEMORY/{category}/L{level}/{slug}.md with collision counter.

## Database
- `DATA/semantic.db` — table `memories` (id, title, summary, embedding, category, level, strength, cycle)

## File Storage
- `MEMORY/{Relations,Knowledge,Events,Self}/L{1,2,3}/*.md`

## Dependencies
- `_paths.py` — DATA, get_cycle
- `embed.py` — HTTP client to embedding service
- `embedding_service.py` — standalone FastAPI server (run separately, not part of MCP)
- History generators read semantic.db by cycle
- Garden reads titles for collision seeds

## Note
- decay tool (aging memories over time) exists in running session but not in this server code. May need building or lives elsewhere.
