# Think Server

Multi-stream cognitive capture. Six streams, 2-3 words each. Input is seed, output is garden.

## Tools
- **stream** — capture cognitive state. All 6 streams required (2-3 words each): cognitive, meta, analytical, creative, relational, predictive.

## How It Works
- Stores all 6 streams as a row in think.db with the current cycle.
- After storing, pulls context from other modules to build a sectioned return:
  - **Meta** — recent thought patterns from think.db
  - **Relational** — heart data for entities mentioned in your relational stream
  - **Predictive** — semantic memories matching your predictive stream
  - **Synthesis** — working memory collisions with your creative/analytical streams
- Early in a system's life, most sections return empty. Think reflects lived experience — no experience yet means quiet returns.

## Database
- `DATA/think.db` — table `thoughts` (id, cycle, cognitive, meta, analytical, creative, relational, predictive)

## External Dependencies
- `_paths.py` — get_cycle
- `pull_meta.py` — reads think.db for recent patterns
- `pull_relational.py` — reads heart.db for entity matches
- `pull_predictive.py` — reads semantic.db for title matches
- `pull_synthesis.py` — reads working.db for thread collisions
- History generators read think.db by cycle
