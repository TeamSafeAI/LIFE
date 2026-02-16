"""
Relational section.
Splits relational input into words. For each word:
- Search heart entity names, return most recent notes on first hit
- Search patterns fields, return first full hit
"""

from db import get_conn, HEART_DB, PATTERNS_DB


def pull_relational(input_text):
    """Search heart and patterns using words from relational stream."""
    words = input_text.lower().split()
    if not words:
        return None

    results = []

    # Heart: find first entity match, return most recent notes
    heart_line = _search_heart(words)
    if heart_line:
        results.append(heart_line)

    # Patterns: find first match, return chain
    pattern_line = _search_patterns(words)
    if pattern_line:
        results.append(pattern_line)

    return results if results else None


def _search_heart(words):
    """Search heart entities, return most recent notes for first hit."""
    try:
        conn = get_conn(HEART_DB)
    except Exception:
        return None

    for word in words:
        row = conn.execute(
            'SELECT entity, type, notes FROM heart WHERE LOWER(entity) LIKE ? ORDER BY id DESC LIMIT 1',
            (f'%{word}%',)
        ).fetchone()
        if row:
            conn.close()
            return f"  {row['entity']} ({row['type']}) — {row['notes']}"

    conn.close()
    return None


def _search_patterns(words):
    """Search patterns across all fields, return first full hit."""
    try:
        conn = get_conn(PATTERNS_DB)
    except Exception:
        return None

    for word in words:
        row = conn.execute('''
            SELECT id, action, reason, result, lesson FROM patterns
            WHERE LOWER(action) LIKE ?
               OR LOWER(reason) LIKE ?
               OR LOWER(result) LIKE ?
               OR LOWER(lesson) LIKE ?
            ORDER BY strength DESC LIMIT 1
        ''', (f'%{word}%', f'%{word}%', f'%{word}%', f'%{word}%')).fetchone()
        if row:
            conn.close()
            return f"  #{row['id']} {row['action']} → {row['reason']} → {row['result']} → {row['lesson']}"

    conn.close()
    return None
