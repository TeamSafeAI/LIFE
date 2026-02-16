"""
Add handler — add note to existing thread, touch cycle.
"""

from db import get_conn, get_cycle


def handle_add(args):
    thread = args.get('thread', '').strip()
    title = args.get('title', '').strip()
    content = args.get('content', '').strip()

    if not thread:
        return [{"type": "text", "text": "thread required."}]
    if not title:
        return [{"type": "text", "text": "title required."}]
    if not content:
        return [{"type": "text", "text": "content required."}]

    conn = get_conn()

    topic = conn.execute('SELECT id FROM topics WHERE title = ?', (thread,)).fetchone()
    if not topic:
        conn.close()
        return [{"type": "text", "text": f"Thread '{thread}' not found."}]

    # Check for duplicate note title
    existing = conn.execute(
        'SELECT id FROM notes WHERE thread_id = ? AND title = ?',
        (topic['id'], title)
    ).fetchone()
    if existing:
        conn.close()
        return [{"type": "text", "text": f"Note '{title}' already exists in '{thread}'."}]

    # Add note
    conn.execute(
        'INSERT INTO notes (thread_id, title, content) VALUES (?, ?, ?)',
        (topic['id'], title, content)
    )

    # Touch thread
    cycle = get_cycle()
    conn.execute('UPDATE topics SET last_touched_cycle = ? WHERE id = ?', (cycle, topic['id']))

    conn.commit()
    conn.close()

    return [{"type": "text", "text": f"Added '{title}' to {thread}."}]
