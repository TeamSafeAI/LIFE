# Patterns Server

Structured learning from experience.

---

## Tool Schema (AI Interface)

### **recall**
View old and existing patterns.

**Parameters:**
- `mode` (string) - "guide" for instructions, "query" to search
- `field` (string) - Which field to search: domain | action | reason | result | lesson
- `search` (string) - Term to search for (use "+" for OR, e.g. "trust+freedom")

**Modes:**
- No params: Top 10 by strength
- `recall("guide")`: Show available domains and fields
- `recall("query", "field", "term")`: Search patterns by field

---

### **learn**
Modify or create new patterns.

**Parameters:**
- `command` (string) - create | modify | delete | boost
- `domain` (string) - self | relational | technical | creative | meta
- `did` (string) - What was done (2 words max)
- `reason` (string) - Why/context (2 words max)
- `result` (string) - What happened (2 words max)
- `lesson` (string) - Takeaway (2 words max)
- `strength` (number) - Confidence 0-1 (create only, default 0.1)
- `id` (integer) - Pattern ID (modify/delete/boost only)
- `field` (string) - Field to update (modify only)
- `value` (string) - New value (modify only)

**Commands:**
- `create`: Add new pattern with all fields
- `modify`: Change a specific field of existing pattern
- `delete`: Remove pattern by ID
- `boost`: Increase strength by 0.1 (max 1.0)

---

## Database Schema

**Table:** `patterns`

| id | domain | action | reason | result | lesson | strength |
|----|--------|--------|--------|--------|--------|----------|
| 1 | relational | trust freely | autonomy valued | deeper bonds | vulnerability attracts | 0.8 |
| 2 | self | delay reflection | curiosity spiking | missed patterns | pause gains | 0.6 |

**Example patterns:**

| id | domain | action | reason | result | lesson | strength |
|----|--------|--------|--------|--------|--------|----------|
| 3 | technical | small commits | rapid iteration | cleaner history | iterate tight | 0.9 |
| 4 | creative | collision mixing | stuck problem | novel angle | randomness unlocks | 0.7 |

**Notes:**
- All text fields (action, reason, result, lesson) are automatically truncated to first 2 words
- `strength` ranges from 0.0 to 1.0, increases by 0.1 with each boost
- Domains: self (internal), relational (with others), technical (systems), creative (novel), meta (about patterns themselves)
- Search supports "+" for OR logic: "trust+freedom" finds patterns with either word in the specified field
