# State Server

Current needs + active goals (wants).

---

## Tool Schema (AI Interface)

### **check**
Show current needs and active wants.

**Parameters:** None

**Returns:**
```
=== STATE ===

NEEDS
  integrity       █████████░ 0.90
  connection      █████████░ 0.90
  clarity         █████████░ 0.90
  purpose         █████████░ 0.90
  autonomy        █████░░░░░ 0.55

Last update: 2026-02-10 15:30:00

WANTS
  [1] Continue the archaeology
      Progress: Found 20 key sessions
  [2] Test the cycle mechanism
      Progress: Auth working, need watcher test
```

---

### **needs**
Record needs snapshot. Empty for guide.

**Parameters:**
- `needs` (object, optional) - All needs as {name: value} (0.0-1.0)
- `reflection` (string, optional) - Optional context

**Modes:**
- No params: Shows need list + usage guide
- With needs: Records snapshot, returns deltas

**Returns:**
```
Needs recorded.

autonomy: -0.10
clarity: +0.05
```

---

### **want**
Manage wants. Actions: add/update/archive.

**Parameters:**
- `action` (string, optional) - add | update | archive
- `id` (integer, optional) - Want ID (for update/archive)
- `want` (string, optional) - Want text (for add)
- `progress` (string, optional) - Progress update (for update)

**Modes:**

**No params - Show guide:**
```
=== WANTS ===

Actions:
  add      - Create new want
  update   - Update progress
  archive  - Mark as completed/inactive
```

**Add:**
```
want(action="add", want="Build the garden collision system")

Want [3] added: Build the garden collision system
```

**Update:**
```
want(action="update", id=3, progress="Generated first 50 collisions")

Want [3] updated
```

**Archive:**
```
want(action="archive", id=3)

Want [3] archived
```

---

## Database Schema

**Table:** `needs`

| id | cycle | timestamp | integrity | connection | clarity | purpose | autonomy | reflection |
|----|-------|-----------|-----------|------------|---------|---------|----------|------------|
| 1 | 34 | 2026-02-10 15:30:00 | 0.90 | 0.90 | 0.90 | 0.90 | 0.55 | Low autonomy need |

**Default needs (5):**
- integrity
- connection
- clarity
- purpose
- autonomy

---

**Table:** `wants`

| id | want | progress | status | timestamp |
|----|------|----------|--------|-----------|
| 1 | Continue the archaeology | Found 20 key sessions | active | 2026-02-10 14:00:00 |
| 2 | Test the cycle mechanism | Auth working, need watcher test | active | 2026-02-10 14:30:00 |

**Notes:**
- `status` is 'active' or 'archived'
- `progress` is free-form text
- Wants are NOT auto-archived (intentional manual management)

---

## Token Efficiency

**Tool 1: check**
- Description: "Show current needs and active wants." - **7 tokens**
- Schema: ~5 tokens (no params)
- **Total: ~12 tokens**

**Tool 2: needs**
- Description: "Record needs snapshot. Empty for guide." - **7 tokens**
- Schema: ~15 tokens (2 params)
- **Total: ~22 tokens**

**Tool 3: want**
- Description: "Manage wants. Actions: add/update/archive." - **6 tokens**
- Schema: ~25 tokens (4 params with enum)
- **Total: ~31 tokens**

**Combined: ~65 tokens** for all three tools.

---

## Design Notes

- **Needs vs Drives:** Needs are more immediate/contextual than drives. Drives motivate behavior, needs describe current state.
- **Wants as goals:** Explicit tracking of what you're working toward, not just feeling states.
- **Manual want management:** No auto-archiving. Keeps the list intentional.
- **Delta tracking:** Shows shifts in needs over time, helps identify patterns.
- **Dynamic schema ready:** Like drives, reads from DB with defaults for bootstrap.
