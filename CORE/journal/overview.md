# Journal Server

First-person narrative. No database — pure filesystem. Entries are .md files in DATA/journal/.

## Tools
- **write** — record a journal entry. Title (2-3 words max, auto-truncated) + content (first-person). Saved as `{title}_{cycle}_{id}.md`.
- **read** — no params: last 10 entry titles. With id: full content of that entry.

## How It Works
- Titles are sanitized: stop words stripped, numbers removed, 40 char max.
- IDs auto-increment by scanning existing filenames for the highest ID.
- Filenames encode title, cycle, and ID for history generators to parse.
- No database — the filesystem IS the storage.

## Database
None.

## External Dependencies
- `_paths.py` — DATA, get_cycle
- History generators parse journal filenames to build day/week/month narratives
