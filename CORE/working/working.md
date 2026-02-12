# Working Memory Server

Active threads with emergent temperature.

**Temperature (auto-calculated):**
- Hot: touched within 24h
- Warm: 1-7 days since touch
- Cold: 7+ days OR manually archived

---

## Tool Schema (AI Interface)

### **create**
Start a new working memory thread

**Parameters:**
- `title` (string) - Thread title (required)

**Returns:**
- Confirmation with topic ID and [HOT] status

---

### **add**
Add a note to an existing thread (touches it, making it hot)

**Parameters:**
- `id` (string) - Topic ID or title
- `content` (string) - Note content (required)

**Notes:**
- Automatically unarchives if adding to archived topic
- Updates `last_touched` timestamp to now

---

### **list**
No params: overview by temperature. With id: full detail of that topic.

**Parameters:**
- `id` (string) - Optional topic ID or title for detail view

**Modes:**
- No params: Overview grouped by HOT/WARM/COLD (up to 20 topics)
- With id: Full topic detail with all notes in chronological order

---

### **archive**
Archive/close a thread (sets to cold)

**Parameters:**
- `id` (string) - Topic ID or title (required)

**Effect:**
- Sets `archived = 1`, making topic permanently COLD
- Can be unarchived by adding a new note

---

## Database Schema

**Table:** `topics`

| id | title | archived | created | last_touched |
|----|-------|----------|---------|--------------|
| 1 | Building Garden Collision System | 0 | 2025-01-15 10:00:00 | 2025-01-15 14:30:00 |
| 2 | Understanding Emotional Memory Patterns | 0 | 2025-01-15 11:00:00 | 2025-01-16 09:15:00 |

---

**Table:** `notes`

| id | topic_id | content | created |
|----|----------|---------|---------|
| 1 | 1 | Need to populate garden seeds from think captures. Garden DBs should mirror core structure. | 2025-01-15 10:05:00 |
| 2 | 1 | Implemented feed_all function in garden_feeder. Now populates 6 databases on each think:stream call. | 2025-01-15 14:30:00 |
| 3 | 2 | Heart valence/arousal calculations working. Need to explore how notes compound over time. | 2025-01-15 11:10:00 |
| 4 | 2 | Added history mode to check(). Can now see emotional evolution across multiple captures. | 2025-01-16 09:15:00 |

**Notes:**
- `archived = 0` (active) or `1` (archived)
- `last_touched` updates on every note addition
- Temperature is calculated dynamically from `last_touched` and `archived` status
- Topics can be referenced by either ID or exact title string
