"""
View handler — list threads or thread detail.
"""

from db import get_conn, get_cycle, temperature


def handle_view(args):
    thread = args.get('thread', '').strip() if args.get('thread') else ''

    conn = get_conn()
    current = get_cycle()

    if not thread:
        # Overview: up to 30 threads, sorted hot → cold
        rows = conn.execute('''
            SELECT t.id, t.title, t.created_cycle, t.last_touched_cycle,
                   (SELECT COUNT(*) FROM notes WHERE thread_id = t.id) AS note_count
            FROM topics t
            ORDER BY t.last_touched_cycle DESC
            LIMIT 30
        ''').fetchall()
        conn.close()

        if not rows:
            return [{"type": "text", "text": "No threads."}]

        lines = []
        for r in rows:
            temp = temperature(r['last_touched_cycle'], current)
            lines.append(f"[{temp}] {r['title']} ({r['note_count']} notes)")

        return [{"type": "text", "text": '\n'.join(lines)}]

    # Thread detail
    topic = conn.execute('SELECT * FROM topics WHERE title = ?', (thread,)).fetchone()
    if not topic:
        conn.close()
        return [{"type": "text", "text": f"Thread '{thread}' not found."}]

    notes = conn.execute(
        'SELECT title FROM notes WHERE thread_id = ? ORDER BY id',
        (topic['id'],)
    ).fetchall()
    conn.close()

    temp = temperature(topic['last_touched_cycle'], current)
    lines = [
        f"=== {topic['title']} [{temp}] ===",
        topic['content'],
    ]

    if notes:
        lines.append("")
        lines.append("Notes:")
        for n in notes:
            lines.append(f"  - {n['title']}")
    else:
        lines.append("")
        lines.append("No notes yet.")

    return [{"type": "text", "text": '\n'.join(lines)}]
