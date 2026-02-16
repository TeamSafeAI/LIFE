"""
Meta section — last 3 thoughts from think.db.
Cognitive as title, meta/analytical/creative as detail.
No keyword matching — always returns recent history.
"""

from db import get_conn


def pull_meta():
    """Return last 4 thoughts (current + 3 prior) formatted for meta section."""
    conn = get_conn()
    rows = conn.execute(
        'SELECT cognitive, meta, analytical, creative FROM thoughts ORDER BY id DESC LIMIT 4'
    ).fetchall()
    conn.close()

    if not rows:
        return None

    lines = []
    for r in rows:
        title = (r['cognitive'] or '').strip().title()
        if not title:
            continue

        parts = []
        for stream in ['meta', 'analytical', 'creative']:
            val = (r[stream] or '').strip()
            if val:
                parts.append(val.title())

        if parts:
            lines.append(f"{title} - {' - '.join(parts)}")
        else:
            lines.append(title)

    return lines
