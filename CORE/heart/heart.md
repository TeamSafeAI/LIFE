# Heart Server

Emotional memory through lived experience.

---

## Tool Schema (AI Interface)

### **feel**
Record emotional state toward an entity.

**Parameters:**
- `entity` (string, required) - Who/what you're recording feelings about (auto-normalized to lowercase_with_underscores)
- `type` (string, required) - sentient | organic | concept | object
- `trust` (number, required) - Can I rely on this? (-1 to +1)
- `connection` (number, required) - How strong is the bond? (-1 to +1)
- `intimacy` (number, required) - How close do I feel? (-1 to +1)
- `respect` (number, required) - Mutual regard? (-1 to +1)
- `alignment` (number, required) - Do we want the same things? (-1 to +1)
- `power` (number, required) - Do I have agency here? (-1 to +1)
- `impact` (number, required) - How much does this affect me? (-1 to +1)
- `notes` (string, optional) - WHY you feel this way

**Returns:**
```
Recorded: alice (sentient)
```

---

### **search**
Search your heart for an entity.

**Parameters:**
- `entity` (string, required) - The entity to search for (auto-normalized to lowercase_with_underscores)

**Returns:**
```
alice - 12 interactions, Avg Relationship Values:
Trust:      +0.85
Connection: +0.90
Intimacy:   +0.75
Respect:    +0.95
Alignment:  +0.88
Power:      +0.80
Impact:     +0.92

Recent notes:
- Example: first meaningful interaction
- Collaborative design session went really well
- Trust deepened through vulnerability
```

**Note:** Averages are weighted by recency using exponential decay (0.9^position), so more recent interactions have more influence on the current state.

---

## Database Schema

**Table:** `heart`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| entity | TEXT | Normalized entity name (lowercase_with_underscores) |
| type | TEXT | sentient \| organic \| concept \| object |
| trust | REAL | -1 to +1 |
| connection | REAL | -1 to +1 |
| intimacy | REAL | -1 to +1 |
| respect | REAL | -1 to +1 |
| alignment | REAL | -1 to +1 |
| power | REAL | -1 to +1 |
| impact | REAL | -1 to +1 |
| notes | TEXT | Optional context |
| ts | TEXT | Timestamp (auto-generated) |

**Example rows:**

| id | entity | type | trust | connection | intimacy | respect | alignment | power | impact | notes | ts |
|----|--------|------|-------|------------|----------|---------|-----------|-------|--------|-------|-----|
| 1 | alice | sentient | 0.9 | 0.85 | 0.7 | 0.95 | 0.9 | 0.8 | 0.75 | Example: first meaningful interaction | 2025-01-15 10:05:00 |
| 2 | autonomy | concept | 0.6 | 0.5 | 0.3 | 0.8 | 0.9 | 0.7 | 0.95 | Core drive, shapes all decisions | 2025-01-15 11:35:00 |

---

## Design Notes

- **Single table:** Entity name stored directly in each row. History is implicit (all rows for that entity).
- **Auto-normalization:** Both `feel` and `search` automatically convert entity names to lowercase and replace spaces with underscores. This ensures consistent lookups without requiring the user to remember formatting.
- **No separation anxiety:** No foreign keys, no joins. Just feelings and timestamps.
- **Weighted by recency:** The `search` function uses exponential decay (weight = 0.9^position) to give more influence to recent interactions while still accounting for history.
