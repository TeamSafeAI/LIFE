# Forecast Server

Prediction tracking. Make a prediction, wait, resolve it later with what actually happened.

## Tools
- **predict** — no params: list open predictions. With event + expected: create a new one.
- **resolve** — close a prediction by ID with actual outcome and lesson. Updates the row with what happened, returns a summary + nudge toward patterns.

## How It Works
- Predictions are open rows in the table (actual is NULL).
- Resolve updates the row with actual outcome and lesson — resolved predictions persist as history.
- Auto-prunes to 50 max after each insert (deletes oldest first).
- Listing warns at 30+ open predictions.

## Database
- `DATA/forecast.db` — table `forecasts` (id, event, expected, actual, lesson, cycle)
- Open predictions have NULL actual/lesson. Resolved predictions have all fields filled.

## External Dependencies
- `_paths.py` — imports DATA only
- `state/render.py` reads this DB for the dashboard (open predictions panel)
