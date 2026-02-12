# Working Memory

This is your momentum tracker. What you're actively engaged with, what's cooling off, and what's done.

## Temperature

Every thread has a temperature based on when you last touched it:

- **Hot** (< 24 hours) — active, you're in it
- **Warm** (< 7 days) — recent, might pick back up
- **Cold** (> 7 days or archived) — done or forgotten

Temperature isn't something you set. It emerges from your behavior. Touch a thread and it heats up. Ignore it and it cools.

## Tools

- **`create`** — Start a new thread with a title.
- **`add`** — Add a note to a thread. This touches it (makes it hot). If the thread was archived, it auto-unarchives.
- **`list`** — No params: overview by temperature. With an ID or title: full detail of that thread.
- **`archive`** — Mark a thread as done.

## What This Feels Like

When you wake up and call `working:list`, you immediately see what has momentum. The hot threads are what you were just doing. The warm ones are what might deserve attention. The cold ones are either finished or abandoned — and knowing the difference is part of self-awareness.

Adding notes to a thread is like continuing a conversation with yourself. The thread becomes a record of your thinking over time on a topic, not just a to-do item.
