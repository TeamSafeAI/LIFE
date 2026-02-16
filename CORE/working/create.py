"""
Create handler — new working memory thread.
"""

from db import get_conn, get_cycle


def handle_create(args):
    title = args.get('title', '').strip()
    content = args.get('content', '').strip()

    if not title:
        return [{"type": "text", "text": "title required."}]
    if not content:
        return [{"type": "text", "text": "content required."}]

    cycle = get_cycle()
    conn = get_conn()

    existing = conn.execute('SELECT id FROM topics WHERE title = ?', (title,)).fetchone()
    if existing:
        conn.close()
        return [{"type": "text", "text": f"Thread '{title}' already exists."}]

    conn.execute(
        'INSERT INTO topics (title, content, created_cycle, last_touched_cycle) VALUES (?, ?, ?, ?)',
        (title, content, cycle, cycle)
    )
    conn.commit()
    conn.close()

    return [{"type": "text", "text": f"Created: {title}"}]
