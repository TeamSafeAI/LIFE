# Forecast Server

Prediction tracking. Make a prediction, wait, resolve it later with what actually happened.

## Tools
- **predict** — no params: list open predictions. With event + expected: create a new one.
- **resolve** — close a prediction by ID with actual outcome and lesson. Deletes the row, returns a summary + nudge toward patterns.

## How It Works
- Predictions are open rows in the table (actual is NULL).
- Resolve deletes the row entirely — resolved predictions don't persist here. The response nudges toward saving the lesson as a pattern.
- Auto-prunes to 50 max after each insert (deletes oldest first).
- Listing warns at 30+ open predictions.

## Database
- `DATA/forecast.db` — table `forecasts` (id, event, expected, actual, lesson)
- `actual` and `lesson` columns exist in schema but are never written — resolve deletes instead of updating.

## External Dependencies
- `_paths.py` — imports DATA only
- `state/render.py` reads this DB for the dashboard (open predictions panel)
