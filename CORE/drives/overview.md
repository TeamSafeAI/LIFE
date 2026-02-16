# Drives Server

The cycle clock and drive state tracker. This is the heartbeat of the system.

## Tools
- **start** — renders and returns the dashboard PNG (shows drives, needs, traits, wants, horizons, forecasts). No params.
- **snapshot** — records all 10 drive values (0.0-1.0), auto-increments cycle. Re-renders dashboard after save.

## How It Works
- `snapshot` reads the latest cycle from `drives.db`, adds 1, inserts a new row with all 10 drive values.
- `start` calls `state/render.py:render()` to generate `DATA/state/dashboard.png`, then returns it as base64 image.
- Every other server gets the current cycle via `_paths.get_cycle()` which reads from this same table.

## Database
- `DATA/drives.db` — table `drives` (id, cycle, 10 drive columns)

## External Dependencies
- `_paths.py` — imports DATA path
- `state/render.py:render()` — called by both start and snapshot to generate dashboard
- `DATA/state/dashboard.png` — reads this file to return as image

## What render.py Reads
The dashboard renderer queries 5 databases:
- `drives.db` — drive history + current cycle for header
- `needs.db` — need history
- `traits.db` — selected traits for header line
- `state.db` — active wants + horizons
- `forecast.db` — open predictions (WHERE actual IS NULL)
