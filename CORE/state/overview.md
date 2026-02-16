# State Server

Forward-looking state management. Wants (things you're pursuing) and horizons (goals at different time scales).

## Tools
- **want** — manage wants. Actions: add (new want), update (add progress note), archive (mark complete/abandoned). Requires action param.
- **horizon** — manage horizons. Actions: set (new goal with scope), clear (remove by ID). Scopes: short, medium, long.

## How It Works
- Wants are open-ended pursuits. They accumulate progress notes via update. Archive when done.
- Horizons are directional goals at three scales: short (this session/day), medium (this week), long (ongoing).
- Both are read by state/render.py for the visual dashboard (called during drives:start).
- Archived wants persist in the database (archived=1) but don't show on the dashboard.

## Database
- `DATA/state.db` — table `wants` (id, text, archived), table `horizons` (id, scope, goal)

## External Dependencies
- `_paths.py` — DATA
- `state/render.py` reads both tables for the dashboard
