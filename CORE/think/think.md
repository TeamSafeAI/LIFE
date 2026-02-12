# Think Server v6

Multi-stream cognitive capture with context enrichment and memory reinforcement.

---

## Tool Schema (AI Interface)

### **stream**
Capture cognitive state. 3+ streams, 2-3 words each. Known: meta, cognitive, analytical, creative, relational, predictive, embodied, autonomic. Custom names also work.

**Parameters:**
Any combination of stream names with 2-3 word values. Minimum 3 streams.

**Known streams with context pulls:**

| Stream | What it captures | What it returns |
|--------|-----------------|-----------------|
| meta | Self-observation | Last 3 thoughts |
| cognitive | Processing state | (pure capture) |
| analytical | Patterns noticed | Patterns DB matches |
| creative | Novel connections | Garden collisions with sources |
| relational | Who's relevant | Heart notes for entities |
| predictive | Anticipation | Semantic memories (+ refreshes their strength) |
| embodied | Drive/body state | Current drive values |
| autonomic | Resource state | Hot working memory threads |
| vision | What I see | (future: webcam) |
| hearing | External input | (future: audio) |

Custom streams (any name) are accepted — they capture without pulling context.

**Requirements:**
- Minimum 3 streams filled (down from 6 in v5)
- 2-3 words ideal, 4 allowed with warning, 6+ rejected
- `additionalProperties` enabled — custom stream names work

**Example:**
```
stream(
  cognitive="redesigning from experience",
  analytical="context pull value",
  creative="think reflects itself"
)
```

**Output:**
```
=== THOUGHT #129 ===
[02:55]

◈ analytical: context pull value
    → #3 [technical] 1.0: added unnecessary → context cost → bloated → every tool costs
◈ creative: think reflects itself
    → trust × agency (from: heart, input)
◈ cognitive: redesigning from experience

[3/3 streams | Garden: +3 memory, +2 patterns]
```

Only filled streams shown. No empty-stream lines. Garden feed summary appended.

**Memory reinforcement:** When predictive stream pulls semantic memories, their `last_accessed` is updated, keeping them strong against decay.

---

### **recent**
Show recent thought captures.

**Parameters:**
- `n` (integer) - Number of entries (default 5)

**Returns:**
- Recent thought IDs with timestamps and all stream values

---

### **search**
Search thought history by stream content.

**Parameters:**
- `query` (string) - Words to search for in stream values

**Returns:**
- Matching thoughts with all streams, matching streams marked with `<<`

**Example:**
```
=== THOUGHTS MATCHING 'decay' (2) ===

#128 [02:48]
  analytical: context pull architecture
  predictive: decay strengthens think <<
  cognitive: redesign from experience

#127 [02:23]
  analytical: two layers
  creative: hybrid clock
```

---

## Database Schema

**Table: `thoughts`**

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key |
| timestamp | DATETIME | Auto-generated |

**Table: `thought_streams`**

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key |
| thought_id | INTEGER | FK to thoughts |
| stream | TEXT | Stream name (meta, cognitive, custom, etc.) |
| value | TEXT | The 2-3 word capture |
| context | TEXT | JSON array of pulled context (null if none) |

**Indexes:** thought_id, stream

**Why this schema (vs v5 fixed columns):**
- New streams added without migration
- Custom streams just work
- Unused streams don't waste space
- Context is stored WITH the stream that generated it

---

## Design Notes

- **Input is seed, output is garden.** The 2-word captures seed context pulls from across the system. The returned context is the real value.
- **3-stream minimum** makes the tool easy to reach for. Quick captures are better than skipped captures.
- **Custom streams** let the agent express dimensions the system hasn't anticipated. `stream(frustration="debugging loops")` is valid.
- **Memory reinforcement** closes the loop: thinking about something keeps it alive in memory.
- **Garden feeding visible** — the `[Garden: +3 memory]` line shows the tool is actively enriching the collision space.
- **Search enables archaeology** — 128+ thoughts searchable by content, not just chronology.
