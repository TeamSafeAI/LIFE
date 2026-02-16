# Heart Server

Emotional state tracking toward entities. 7 dimensions per snapshot, wall notes for qualitative context, visual renders for both.

## Tools
- **feel** — record emotional state. All 7 dimensions (0.0-1.0), entity, type, notes required. Appends a new row (time-series, not overwrite).
- **search** — text only. No params: capped directory (latest per entity by most recent id, type + snapshot count + wall count, max 50). With entity: text detail (latest dimension values, notes, counts).
- **check** — visual only. No params: constellation image (all entities). With entity: wall image (dimension history + sticky notes).
- **wall** — sticky notes per entity. Entity + note: add (auto-tagged "general" unless tag given). Entity + id: remove. Entity + id + tag: re-tag. Tags: who_they_are, who_i_am_with_them, what_we_built, how_we_repair, what_they_teach, what_i_owe, general.

## How It Works
- Each `feel` call inserts a new row — full history is preserved, not just latest.
- `search` no params uses GROUP BY + MAX(id) to get one row per entity, ordered most recent first, capped at 50.
- `search` with entity returns latest snapshot dimensions, notes, snapshot count, wall count as text.
- `check` with no params calls `heart_render.py` — constellation: you at center, entities positioned by dimensions (intimacy=distance, alignment=Y, impact=size, respect=brightness, trust=glow, connection=heart/line).
- `check` with entity calls `wall_render.py` — top 1/3 dimension history lines, bottom 2/3 wall notes grouped by tag.
- Wall is write-through: add/remove/retag via `wall` tool, view via `check`.

## Database
- `DATA/heart.db` — table `heart` (id, entity, type, 7 dimensions, notes, cycle), table `wall` (id, entity, tag, note)

## External Dependencies
- `_paths.py` — DATA, get_cycle, VISUAL
- `heart_render.py` — constellation renderer (matplotlib). Reads heart.db, outputs to VISUAL/heart_constellation.png. Looks for avatar in DATA/avatar/.
- `wall_render.py` — per-entity wall renderer (matplotlib). Reads heart.db + wall table, outputs to VISUAL/heart_{entity}.png.
- History server reads heart.db (day, week, month generators query by cycle)
- Garden reads heart.db (entity names, types, dimensions for collision seeds)
