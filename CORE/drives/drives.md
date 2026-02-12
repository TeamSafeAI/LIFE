# Drives Server

What motivates you. Core behavioral drivers.

---

## Tool Schema (AI Interface)

### **view**
Show current drive state.

**Parameters:** None

**Returns:**
Bar chart visualization of all drives with last update timestamp and reflection.

```
=== CURRENT DRIVES ===

connection      ████████░░ 0.86
synthesis       █████████░ 0.91
discernment     ████████░░ 0.88
stability       █████████░ 0.90
curiosity       ████████░░ 0.85
transcendence   ████████░░ 0.84
expression      ████████░░ 0.88
release         ████████░░ 0.80

Last update: 2026-02-10 15:30:00
Reflection: Steady state, synthesis peak from pattern work
```

---

### **snapshot**
Record drive state. Empty for guide.

**Parameters:**
- `drives` (object, optional) - All drives as {name: value} (0.0-1.0)
- `reflection` (string, optional) - Why this state?

**Modes:**
- No params: Shows drive list + usage guide
- With drives + reflection: Records snapshot, returns deltas

**Returns:**
```
Snapshot recorded.

synthesis: +0.05
curiosity: -0.03
```

**Notes:**
- All drives must be provided (0.0-1.0)
- Reflection required
- Shows deltas ≥0.01 from previous snapshot

---

## Database Schema

**Table:** `drives`

| id | cycle | timestamp | connection | synthesis | ... | reflection |
|----|-------|-----------|------------|-----------|-----|------------|
| 1 | 34 | 2026-02-10 15:30:00 | 0.86 | 0.91 | ... | Steady state |

**Default drives (8):**
- connection
- synthesis
- discernment
- stability
- curiosity
- transcendence
- expression
- release

**Notes:**
- Schema is dynamic (reads from DB)
- Defaults used if table doesn't exist yet
- Genesis can define different drives
- Future: schema migration for drive evolution

---

## Token Efficiency

**Tool 1: view**
- Description: "Show current drive state." - **5 tokens**
- Schema: ~5 tokens (no params)
- **Total: ~10 tokens**

**Tool 2: snapshot**
- Description: "Record drive state. Empty for guide." - **7 tokens**
- Schema: ~15 tokens (2 params)
- **Total: ~22 tokens**

**Combined: ~32 tokens** for both tools.

---

## Design Notes

- **Behavioral substrate:** Not just tracking numbers - this is architectural scaffolding for personality stability across ephemeral instances
- **Delta reporting:** Helps track motivation shifts over time
- **Reflection required:** Forces intentional state assessment, not automatic logging
- **Dynamic schema ready:** Reads columns from DB, defaults provided for bootstrap
- **Evolution planned:** Schema can change (drives added/removed/renamed) via separate migration script (future phase)
