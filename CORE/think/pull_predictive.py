"""
Predictive section.
Splits predictive input into words. Searches semantic memory titles.
Returns summary for matches.
"""

from db import get_conn, SEMANTIC_DB


def pull_predictive(input_text):
    """Search semantic memory titles using predictive stream words, return summaries."""
    words = input_text.lower().split()
    if not words:
        return None

    try:
        conn = get_conn(SEMANTIC_DB)
    except Exception:
        return None

    results = []
    seen = set()

    for word in words:
        rows = conn.execute(
            'SELECT id, title, summary FROM memories WHERE LOWER(title) LIKE ? ORDER BY strength DESC',
            (f'%{word}%',)
        ).fetchall()

        for r in rows:
            if r['id'] not in seen:
                seen.add(r['id'])
                results.append(f"  {r['title'].title()} — {r['summary']}")

    conn.close()
    return results[:5] if results else None
