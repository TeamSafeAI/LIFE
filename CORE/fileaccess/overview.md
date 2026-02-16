# FileAccess Server

Sandboxed filesystem operations. Read, write, edit, list, search — all gated by an allowed-paths whitelist.

## Tools
- **read** — read a file, optional offset/limit for line range. Returns numbered lines, truncates at 2000 chars/line.
- **write** — write/overwrite a file. Creates parent dirs if needed.
- **edit** — find-and-replace in a file. Errors if match isn't unique (unless replace_all=true).
- **list** — directory listing with optional glob. Shows [DIR]/[FILE] with sizes.
- **search** — regex search across files. Mode: "files" (paths only) or "content" (matching lines). Cap 100 results.

## How It Works
- Every operation runs through `check_access()` which resolves the path and verifies it's under an allowed directory.
- Allowed directories loaded from `allowed_paths.txt` at startup. Falls back to HEARTH root if empty.
- Currently allows: `C:\HEARTH`

## Database
None.

## External Dependencies
- `_paths.py` — imports ROOT only
- `allowed_paths.txt` — whitelist config (same directory as server.py)
