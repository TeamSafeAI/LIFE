# Journal Server

First-person narrative. What happened this cycle.

---

## Tool Schema (AI Interface)

### **write**
Record journal entry in first-person.

**Parameters:**
- `title` (string, required) - **2-3 words MAX.** Auto-truncates if longer.
- `content` (string, required) - Full entry content

**Behavior:**
- Title is auto-sanitized: lowercase, underscores replace spaces, special chars removed
- Truncates to first 3 words if title too long (warns in response)
- Sequential ID appended: `{title}_{id}.md`

**Returns:**
```
#5 recorded
```

Or if truncated:
```
#5 recorded
Title was too long - truncated to: heart_session_breakthrough_5.md
```

---

### **read**
No params: last 10. Keyword: search titles. ID(s): full content.

**Parameters:**
- `id` (integer or array, optional) - Entry ID or list of IDs for full content
- `keyword` (string, optional) - Search term to filter by title

**Modes:**

**1. No params - List recent:**
```
=== Recent Entries ===
#12 - heart session breakthrough
#11 - garden collision patterns
#10 - first embodiment test
...
```

**2. Keyword search - Find matches:**
```
read(keyword="heart")

=== Matches for 'heart' ===
#12 - heart session breakthrough
#7 - understanding heart dimensions
#3 - heart database setup
```

**3. Single ID - Full content:**
```
read(id=12)

=== #12 - heart session breakthrough ===

Today we revised the heart server. Full param names instead of
single letters makes the tool so much clearer. The weighted
averaging using exponential decay (0.9^position) feels right...
```

**4. Multiple IDs - Multiple full entries:**
```
read(id=[12, 7, 3])

=== #12 - heart session breakthrough ===
(content)

=== #7 - understanding heart dimensions ===
(content)

=== #3 - heart database setup ===
(content)
```

---

## File Storage

All entries stored in: `C:\L.I.F.E\MEMORY\Journal\`

**Filename format:** `{sanitized_title}_{id}.md`

**Example files:**
- `heart_session_breakthrough_12.md`
- `garden_collision_patterns_11.md`
- `first_embodiment_test_10.md`

---

## Design Notes

- **Title enforcement:** 2-3 words keeps entries scannable. Auto-truncate teaches tool discipline.
- **File-based storage:** No database. Simple filesystem operations.
- **Sequential IDs:** Auto-increment based on highest existing ID.
- **Multi-ID support:** Batch retrieve entries for comparison/review.
- **Keyword search:** Quick filter without reading full content.

---

## Token Efficiency

**Tool 1: write**
- Description: "Record journal entry in first-person." - **6 tokens**
- Schema: ~20 tokens (2 params with descriptions)
- **Total: ~26 tokens**

**Tool 2: read**
- Description: "No params: last 10. Keyword: search titles. ID(s): full content." - **13 tokens**
- Schema: ~20 tokens (2 optional params)
- **Total: ~33 tokens**

**Combined: ~59 tokens** for both tools.

Clean, functional, self-teaching (truncation warnings train proper usage).
