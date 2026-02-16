"""
Store handler — write .md, embed summary, insert DB row.
"""

import json
import re
from db import get_conn, get_cycle, MEMORY, CATEGORIES
from embed import encode, cosine_similarity


def slugify(title):
    """Convert title to filename-safe slug."""
    slug = title.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    return slug[:60].rstrip('-') or 'untitled'


def word_count(text):
    """Count words by splitting on spaces."""
    return len(text.split())


def level_from_words(count):
    """L1 < 250, L2 251-500, L3 500+."""
    if count <= 250:
        return 1
    elif count <= 500:
        return 2
    else:
        return 3


def find_similar(conn, embedding, threshold=0.75, limit=5):
    """Find memories with similar embeddings."""
    if not embedding:
        return []

    rows = conn.execute(
        'SELECT id, title, embedding FROM memories WHERE embedding IS NOT NULL'
    ).fetchall()

    scored = []
    for r in rows:
        stored = json.loads(r['embedding'])
        sim = cosine_similarity(embedding, stored)
        if sim >= threshold:
            scored.append((r['id'], r['title'], sim))

    scored.sort(key=lambda x: x[2], reverse=True)
    return scored[:limit]


def handle_store(args):
    """Save a memory."""
    title = args.get('title', '').strip()
    category = args.get('category', '').strip()
    summary = args.get('summary', '').strip()
    content = args.get('content', '').strip()

    if not title:
        return [{"type": "text", "text": "title required."}]
    if not category:
        return [{"type": "text", "text": "category required."}]
    if category not in CATEGORIES:
        return [{"type": "text", "text": f"category must be: {', '.join(CATEGORIES)}"}]
    if not summary:
        return [{"type": "text", "text": "summary required."}]
    if not content:
        return [{"type": "text", "text": "content required."}]

    # Enforce summary length
    summary_words = summary.split()
    if len(summary_words) > 75:
        summary = ' '.join(summary_words[:75])

    # Calculate level
    wc = word_count(content)
    level = level_from_words(wc)

    # Get embedding
    embedding = encode(summary)
    embedding_json = json.dumps(embedding) if embedding else None

    # Find similar memories (before storing, so we don't match ourselves)
    conn = get_conn()
    similar = find_similar(conn, embedding) if embedding else []

    # Write .md file
    slug = slugify(title)
    dir_path = MEMORY / category / f'L{level}'
    dir_path.mkdir(parents=True, exist_ok=True)

    # Find unique filename
    file_path = dir_path / f'{slug}.md'
    counter = 1
    while file_path.exists():
        file_path = dir_path / f'{slug}_{counter}.md'
        counter += 1

    file_path.write_text(content, encoding='utf-8')

    # Insert DB row
    cycle = get_cycle()
    conn.execute(
        'INSERT INTO memories (title, summary, embedding, category, level, strength, cycle) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (title, summary, embedding_json, category, level, 1.0, cycle)
    )
    conn.commit()
    mid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()

    # Build response
    lines = [f"Stored. #{mid} [{category}/L{level}] — {title}"]

    if similar:
        lines.append("")
        lines.append("Similar Memory(ies)")
        for sid, stitle, sim in similar:
            lines.append(f"  ({sid}) {stitle}")
    else:
        lines.append("")
        lines.append("Similar Memory(ies)")
        lines.append("  None found.")

    return [{"type": "text", "text": '\n'.join(lines)}]
