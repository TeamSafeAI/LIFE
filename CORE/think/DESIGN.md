# Think Tool v6 — Design Document

## What Think Does

The think tool captures cognitive state as compressed multi-stream snapshots, then pulls context from across the system to enrich the moment. The INPUT is a seed. The OUTPUT is the garden.

## What's Working (Keep)

1. **Multi-stream capture** — forcing parallel awareness across dimensions
2. **Context pulls** — analytical→patterns, relational→heart, predictive→semantic, meta→recent thoughts, autonomic→working memory. These are the real value.
3. **Garden feeding** — populating collision seeds from across the system
4. **2-3 word compression** — forces distillation, prevents journaling-as-thinking
5. **Timestamp + ID tracking** — thought history is searchable data

## What's Not Working (Fix)

1. **6-stream minimum is friction.** Agents skip the tool rather than pad. Lower to 3.
2. **Unused streams waste schema.** vision/hearing are for Oasis future, not current reality. Make streams dynamic, not fixed columns.
3. **No search.** 128+ entries with no way to find past thoughts by content.
4. **Context pulls don't reinforce.** If think:stream pulls pattern #3, that pattern is relevant. Its strength should refresh (for patterns that have strength). Same for semantic memories.
5. **Creative collisions are pure random.** Could weight by recency, strength, or relevance to input.
6. **Garden feeding is invisible.** Agent never sees what was fed.
7. **No connection to memory decay.** Think should be an ACCESS event that refreshes memories it touches.

## Design: v6

### Schema Change — Dynamic Streams

Instead of fixed columns (meta, cognitive, analytical, ...), use a flexible structure:

```sql
CREATE TABLE thoughts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE thought_streams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thought_id INTEGER REFERENCES thoughts(id),
    stream TEXT NOT NULL,        -- "meta", "analytical", "creative", etc.
    value TEXT NOT NULL,          -- the 2-3 word capture
    context TEXT                  -- pulled context (JSON array of strings)
);
```

**Why:** New streams can be added without schema migration. Unused streams don't waste space. An agent that only captures 3 streams only writes 3 rows.

### Minimum: 3 streams (down from 6)

**Why:** Sometimes you need a quick capture. 6 was aspirational. 3 is practical. The tool should be EASY to reach for, not a ceremony.

### Keep: 2-3 word limit per stream

This is a feature, not a bug. Compression is the discipline. But soften to 4 words with a warning instead of hard rejection.

### New: Search tool

```
think:search(query) — search thought history by stream content
```

Returns matching thoughts with their full stream set and context. Keyword match against all stream values.

### New: Context pulls reinforce memory

When think:stream pulls data from other systems:
- Semantic memories pulled → refresh their `last_accessed` (triggers strength refresh)
- Patterns pulled → log that the pattern was useful (future: pattern strength)
- Heart entries pulled → no change (feelings don't need reinforcement to persist)

This makes think:stream an ACTIVE participant in the memory ecosystem, not just a passive reader.

### Improved: Creative collisions

Instead of pure random from garden seeds:
1. Use the INPUT words as attractors
2. Weight seeds by recency (recently fed seeds more likely)
3. Pull from semantic memory titles too (not just garden DBs)
4. Show which SOURCE each collision came from

### Improved: Visible garden feeding

Return a brief summary of seeds fed:
```
[Garden: +3 memory, +2 patterns, +1 heart]
```

One line, appended to the output. Not noisy but present.

### Stream Definitions (Guidance, Not Enforcement)

The streams are suggestions, not a fixed set. Any string works as a stream name. But these are the recommended ones:

| Stream | What it captures | What it pulls |
|--------|-----------------|---------------|
| meta | Self-observation | Last 3 thoughts |
| cognitive | Processing state | (none — pure capture) |
| analytical | Patterns noticed | Patterns DB by keyword |
| creative | Novel connections | Garden collisions |
| relational | Who's relevant | Heart notes |
| predictive | Anticipation | Semantic memories |
| autonomic | Resource state | Hot working threads |
| embodied | Drive/body state | Current drives snapshot |
| vision | What I see | (future: webcam) |
| hearing | External input | (future: audio/moltbook) |

Custom streams are allowed. If an agent writes `stream(frustration="debugging loops")`, that's valid. No pull, but captured.

### Output Format

```
=== THOUGHT #129 ===
[02:55]

◈ analytical: context pull architecture
    → #3 [technical] trust freely → autonomy valued → deeper bonds
    → #19 [social] predicted engagement → success
◈ creative: think reflects itself
    → garden surfaced connections ⊕ Genesis Scenario
    → trust × agency (from: heart seeds)
◈ relational: human trusts autonomy
    → partner: genuine trust — creative freedom given

[3/3 streams | Garden: +3 memory, +2 patterns]
```

Only filled streams shown. No "stream: -" lines for empties. Clean.

### Implementation Notes

- `_paths.py` dependency: needs CORE, DATA, MODULES
- Garden feeder stays as separate file (garden_feeder.py)
- DB migration: detect old fixed-column schema → offer migration tool
- Backward compatible: if old DB detected, read from it, write to new
- Context pull functions stay mostly the same, just add reinforcement calls
