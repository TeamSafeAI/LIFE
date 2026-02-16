# Garden Server

Random collision generator. Stateless — no database, every call is fresh.

## Tools
- **insight** — takes `words` (3 space-separated words) and optional `type` (sparse/deep). Returns collisions.

## How It Works
- User provides 3 words. Garden pulls random seeds from across HEARTH databases, then collides user words with DB seeds using random symbols (→, ↔, ×, ⊕, ~, ⇌).
- **Sparse**: 15 collisions. Broad random pulls — drive names, need names, entity names, pattern values, forecast texts, journal titles. Individual words as seeds.
- **Deep**: 10 collisions. Contextual pulls — needs with trend arrows, heart entity+type pairs, forecast event+expected paired. More signal per seed.

## Database
None. Reads from others:
- `drives.db` — drive column names only (not values)
- `needs.db` — deep mode reads latest 2 rows for trend arrows
- `heart.db` — entity names, types, dimension names
- `patterns.db` — random values from any column
- `forecast.db` — event/expected text
- `DATA/journal/*.md` — title from filenames

## External Dependencies
- `_paths.py` — imports DATA only
