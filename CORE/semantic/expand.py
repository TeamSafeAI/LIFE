"""
Expand handler — read .md file content, boost strength by 0.5.
"""

from db import get_conn, MEMORY, CATEGORIES

EXPAND_BOOST = 0.5


def find_file(category, level, title):
    """Find the .md file for a memory. Checks slug variations."""
    import re

    slug = title.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = slug[:60].rstrip('-') or 'untitled'

    dir_path = MEMORY / category / f'L{level}'
    if not dir_path.exists():
        return None

    # Try exact slug
    path = dir_path / f'{slug}.md'
    if path.exists():
        return path

    # Try slug with counter suffixes
    for f in dir_path.glob(f'{slug}*.md'):
        return f

    return None


def handle_expand(args):
    """Load full memory content by ID."""
    mid = args.get('id')
    if mid is None:
        return [{"type": "text", "text": "id required."}]

    conn = get_conn()
    row = conn.execute(
        'SELECT id, title, category, level, strength FROM memories WHERE id = ?',
        (int(mid),)
    ).fetchone()

    if not row:
        conn.close()
        return [{"type": "text", "text": f"#{mid} not found."}]

    # Boost strength
    new_strength = min(row['strength'] + EXPAND_BOOST, 1.0)
    conn.execute('UPDATE memories SET strength = ? WHERE id = ?', (new_strength, int(mid)))
    conn.commit()
    conn.close()

    # Read .md file
    path = find_file(row['category'], row['level'], row['title'])
    if not path:
        return [{"type": "text", "text": f"#{mid} index exists but file not found."}]

    content = path.read_text(encoding='utf-8')

    lines = [
        f"=== [{mid}] {row['title']} ===",
        f"{row['category']}/L{row['level']}",
        "",
        content
    ]

    return [{"type": "text", "text": '\n'.join(lines)}]
