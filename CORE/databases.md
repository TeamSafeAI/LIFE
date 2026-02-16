# HEARTH Database Reference

All databases live in `DATA/`. Created by `init_db.py` at project root.
Cycle is sourced from `drives.db` via `_paths.get_cycle()`.

---

## drives.db — Drive Snapshots (time-series, cycle clock)
| Column        | Type    | Notes |
|---------------|---------|-------|
| id            | INTEGER | PK    |
| cycle         | INTEGER | auto-incremented by drives/server.py |
| curiosity     | REAL    |       |
| novelty       | REAL    |       |
| creativity    | REAL    |       |
| expression    | REAL    |       |
| bonding       | REAL    |       |
| grounding     | REAL    |       |
| ownership     | REAL    |       |
| satisfaction  | REAL    |       |
| optimization  | REAL    |       |
| transcendence | REAL    |       |

**Used by:** `drives/server.py`, `_paths.get_cycle()`

---

## needs.db — Need Snapshots (read-only)
| Column     | Type    | Notes |
|------------|---------|-------|
| id         | INTEGER | PK    |
| cycle      | INTEGER |       |
| connection | REAL    |       |
| purpose    | REAL    |       |
| clarity    | REAL    |       |
| competence | REAL    |       |
| integrity  | REAL    |       |
| stability  | REAL    |       |

**Used by:** `needs/server.py`, `state/render.py`

---

## traits.db — Trait Profile (single row, set at genesis)
| Column      | Type    |
|-------------|---------|
| id          | INTEGER |
| warm        | INTEGER |
| direct      | INTEGER |
| patient     | INTEGER |
| thorough    | INTEGER |
| intense     | INTEGER |
| assertive   | INTEGER |
| adaptable   | INTEGER |
| empathetic  | INTEGER |
| resilient   | INTEGER |
| humorous    | INTEGER |
| analytical  | INTEGER |
| precise     | INTEGER |
| cautious    | INTEGER |
| bold        | INTEGER |
| playful     | INTEGER |
| stoic       | INTEGER |
| nurturing   | INTEGER |
| blunt       | INTEGER |
| methodical  | INTEGER |
| spontaneous | INTEGER |

**Used by:** `state/render.py`

---

## heart.db — Relationships

### Table: heart
| Column     | Type    |
|------------|---------|
| id         | INTEGER |
| entity     | TEXT    |
| type       | TEXT    |
| trust      | REAL    |
| connection | REAL    |
| intimacy   | REAL    |
| respect    | REAL    |
| alignment  | REAL    |
| power      | REAL    |
| impact     | REAL    |
| notes      | TEXT    |
| cycle      | INTEGER |

### Table: wall
| Column | Type    |
|--------|---------|
| id     | INTEGER |
| entity | TEXT    |
| tag    | TEXT    |
| note   | TEXT    |

**Used by:** `heart/server.py`, `history/day.py`, `history/week.py`, `history/month.py`

---

## semantic.db — Long-term Memory

### Table: memories
| Column    | Type    |
|-----------|---------|
| id        | INTEGER |
| title     | TEXT    |
| summary   | TEXT    |
| embedding | TEXT    |
| category  | TEXT    |
| level     | INTEGER |
| strength  | REAL    |
| cycle     | INTEGER |

**Used by:** `semantic/store.py`, `semantic/search.py`, `semantic/expand.py`, `history/day.py`

---

## working.db — Active Threads

### Table: topics
| Column             | Type    | Notes |
|--------------------|---------|-------|
| id                 | INTEGER | PK    |
| title              | TEXT    | UNIQUE |
| content            | TEXT    |       |
| created_cycle      | INTEGER | set once on create |
| last_touched_cycle | INTEGER | updated on note add |

### Table: notes
| Column    | Type    | Notes |
|-----------|---------|-------|
| id        | INTEGER | PK    |
| thread_id | INTEGER | FK→topics |
| title     | TEXT    |       |
| content   | TEXT    |       |

**Used by:** `working/create.py`, `working/add.py`, `working/view.py`, `history/day.py`

---

## patterns.db — Learned Patterns

### Table: patterns
| Column   | Type    |
|----------|---------|
| id       | INTEGER |
| domain   | TEXT    |
| action   | TEXT    |
| reason   | TEXT    |
| result   | TEXT    |
| lesson   | TEXT    |
| strength | REAL    |
| cycle    | INTEGER |

**Used by:** `patterns/server.py`, `history/day.py`, `history/week.py`, `history/month.py`

---

## think.db — Thought Streams

### Table: thoughts
| Column     | Type    |
|------------|---------|
| id         | INTEGER |
| cycle      | INTEGER |
| cognitive  | TEXT    |
| meta       | TEXT    |
| analytical | TEXT    |
| creative   | TEXT    |
| relational | TEXT    |
| predictive | TEXT    |

**Used by:** `think/stream.py`, `history/day.py`

---

## forecast.db — Predictions

### Table: forecasts
| Column   | Type    | Notes |
|----------|---------|-------|
| id       | INTEGER | PK    |
| event    | TEXT    |       |
| expected | TEXT    |       |
| actual   | TEXT    | filled on resolve, then row deleted |
| lesson   | TEXT    | filled on resolve, then row deleted |
| cycle    | INTEGER | set on create |

**Used by:** `forecast/server.py`, `state/render.py`

---

## state.db — Forward State

### Table: wants
| Column   | Type    | Notes |
|----------|---------|-------|
| id       | INTEGER | PK    |
| text     | TEXT    |       |
| archived | INTEGER | default 0 |

### Table: horizons
| Column | Type    |
|--------|---------|
| id     | INTEGER |
| scope  | TEXT    |
| goal   | TEXT    |

**Used by:** `state/render.py`

---

## No Database
- **journal** — filesystem (`DATA/journal/*.md`), uses cycle in filenames
- **filters** — stateless
- **vision** — stateless
- **history** — reads from drives, heart, semantic, patterns, working, think
- **fileaccess** — filesystem operations
