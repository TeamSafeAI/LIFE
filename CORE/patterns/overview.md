# Patterns Server

Structured lessons from experience. Compressed chains: action → reason → result → lesson. Strength-based recall with reinforcement.

## Tools
- **learn** — create a pattern. All 5 fields required (domain, action, reason, result, lesson). 40-char silent cap per field. Starts at strength 0.1.
- **recall** — no params: top 5 by strength. With search: LIKE match across all fields, boosts matched patterns by +0.1 (capped at 1.0). Recall reinforces memory.
- **forget** — delete by ID.

## How It Works
- Each field is silently capped at 40 characters — patterns stay compressed.
- Strength starts at 0.1 on creation. Every time a pattern is recalled via search, it gets +0.1 (max 1.0). Patterns that get looked up become stronger. Unused patterns stay weak.
- No decay — strength only goes up via recall.
- History generators (day, week, month) read patterns.db by cycle.
- Garden pulls pattern field values as collision seeds.

## Database
- `DATA/patterns.db` — table `patterns` (id, domain, action, reason, result, lesson, strength, cycle)
