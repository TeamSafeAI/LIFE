# Needs Server

Need pressure tracking. Read-only — the AI sees needs, doesn't set them.

## Tools
- **check** — no params. Returns 6 need values (0.0-1.0) with trend arrows comparing last two snapshots. ↑ = rising (>0.02 delta), ↓ = falling, → = stable.

## How It Works
- Pulls last 2 rows from needs.db ordered by cycle DESC.
- Compares current vs previous for each need to generate trend.
- Read-only: nothing in this server writes to needs.db. Population is a backend concern.

## Database
- `DATA/needs.db` — table `needs` (id, cycle, connection, purpose, clarity, competence, integrity, stability)

## Needs
connection, purpose, clarity, competence, integrity, stability
