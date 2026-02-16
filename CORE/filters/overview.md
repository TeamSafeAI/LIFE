# Filters Server

Stateless deliberation prompts for slow thinking. No database, no state. Just returns text.

## Tools
- **filter** — takes a `type` param, returns the corresponding deliberation prompt.

## Filter Types
Main (4): doubt, ethics, stakes, intuition
Secondary (4): memory, logic, alternatives, confirm
Special: "more" — lists secondary filter names

## How It Works
- Prompts are hardcoded in `filters.py` as two dicts (MAIN and SECONDARY).
- `get_filter()` looks up the type, returns the prompt text. Unknown types get an error listing available options.
- Completely stateless. No database, no filesystem, no cross-module imports.

## Database
None.

## External Dependencies
None. Only imports from its own `filters.py`.

## Check
- Running session has 8 separate tools (one per filter, no params). Code on disk has 1 tool with a type param. Mismatch — one of these needs updating.
