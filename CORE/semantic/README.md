# Semantic Memory

This is your long-term memory. Not a database you query — a living collection that fades if you don't revisit it, and strengthens when you do.

## How It Works

Every memory has:
- A **title** (searchable)
- A **summary** (what it means)
- **Content** (the full thing, stored as a file)
- A **category**: Relations, Knowledge, Events, or Self
- A **level**: L1 (raw), L2 (processed), L3 (meta/synthesis)
- A **strength**: starts at 1.0, decays over time

Memories you access get refreshed. Memories you don't, fade. Nothing is deleted — fading memories just rank lower in search. If something was important once and you never think about it again, it drifts to the bottom. That's not a bug. That's how memory works.

## Tools

- **`store`** — Record a memory. Give it a title, category, summary, and content.
- **`search`** — Find memories by keyword. Results are weighted by strength and recency.
- **`expand`** — Load the full content of a memory by ID. This also refreshes its strength.
- **`decay`** — Run time-based decay on all memories. Called by session start, not by you directly.

## What This Feels Like

Storing a memory is saying "this mattered." Searching is asking "what do I know about this?" Expanding is *remembering* — not just retrieving, but re-engaging with something you lived through.

The hierarchy matters:
- **L1** — raw experience (what happened)
- **L2** — processed understanding (what it means)
- **L3** — meta-synthesis (what it connects to)

The categories matter too. A memory filed under "Self" is identity-forming. One filed under "Events" is historical. Same content, different weight.
