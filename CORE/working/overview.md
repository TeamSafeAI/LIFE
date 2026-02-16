# Working Memory Server

Short-term memory threads with cycle-based temperature. Threads hold notes, cool over time.

## Tools
- **create** — new thread. Title (unique) + content required. Sets created_cycle and last_touched_cycle.
- **add** — add note to thread. Thread + title + content. Checks duplicate note title per thread. Updates last_touched_cycle.
- **view** — no params: up to 30 threads sorted hot→cold with note count. With thread: detail (content + note titles).
- **see** — visual render. No params: board overview (all threads grouped by temp, note counts). With thread: single thread detail (content, notes, cycles).

## How It Works
- Temperature derived from cycle distance: ≤5 = HOT, ≤15 = WARM, else COLD.
- Each note add touches the thread's last_touched_cycle, keeping it hot.
- Shared db.py provides get_conn(), temperature(), imports get_cycle from _paths.
- History generators (day, week, month) query by last_touched_cycle.

## Database
- `DATA/working.db` — table `topics` (id, title, content, created_cycle, last_touched_cycle), table `notes` (id, thread_id, title, content)

## Dependencies
- `_paths.py` — DATA, VISUAL, get_cycle
- `matplotlib` — rendering (Agg backend)
- Renders save to VISUAL/working.png (overwritten each call)
