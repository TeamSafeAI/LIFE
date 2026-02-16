"""
Search handler — keyword + semantic search, boost 0.1 on hit.
"""

import json
from db import get_conn
from embed import encode, cosine_similarity

SEARCH_BOOST = 0.1


def keyword_search(conn, query, limit=5):
    """Match query against title column. Up to limit results."""
    term = f'%{query}%'
    rows = conn.execute(
        'SELECT id, title FROM memories WHERE title LIKE ? ORDER BY id DESC LIMIT ?',
        (term, limit)
    ).fetchall()
    return [(r['id'], r['title']) for r in rows]


def semantic_search(conn, query, limit=5):
    """Embed query, cosine similarity against all embeddings. Top limit results."""
    query_embedding = encode(query)
    if not query_embedding:
        return []

    rows = conn.execute(
        'SELECT id, title, embedding FROM memories WHERE embedding IS NOT NULL'
    ).fetchall()

    scored = []
    for r in rows:
        stored = json.loads(r['embedding'])
        sim = cosine_similarity(query_embedding, stored)
        scored.append((r['id'], r['title'], sim))

    scored.sort(key=lambda x: x[2], reverse=True)
    return [(sid, stitle) for sid, stitle, _ in scored[:limit]]


def boost_results(conn, ids):
    """Small boost on search hit."""
    for mid in ids:
        conn.execute(
            'UPDATE memories SET strength = MIN(strength + ?, 1.0) WHERE id = ?',
            (SEARCH_BOOST, mid)
        )
    conn.commit()


def handle_search(args):
    """Search memories."""
    query = args.get('query', '').strip() if args.get('query') else ''

    conn = get_conn()

    if not query:
        # Last 10 by recency
        rows = conn.execute(
            'SELECT id, title FROM memories ORDER BY id DESC LIMIT 10'
        ).fetchall()
        conn.close()

        if not rows:
            return [{"type": "text", "text": "No memories yet."}]

        lines = [f"({r['id']}) {r['title']}" for r in rows]
        return [{"type": "text", "text": '\n'.join(lines)}]

    # Two passes
    kw_results = keyword_search(conn, query, limit=5)
    sem_results = semantic_search(conn, query, limit=5)

    # Deduplicate — keyword first
    seen = set()
    combined = []
    for mid, title in kw_results:
        if mid not in seen:
            seen.add(mid)
            combined.append((mid, title))
    for mid, title in sem_results:
        if mid not in seen:
            seen.add(mid)
            combined.append((mid, title))

    if not combined:
        conn.close()
        return [{"type": "text", "text": f"No memories matching '{query}'."}]

    # Boost all hit IDs
    boost_results(conn, [mid for mid, _ in combined])
    conn.close()

    lines = [f"({mid}) {title}" for mid, title in combined]
    return [{"type": "text", "text": '\n'.join(lines)}]
