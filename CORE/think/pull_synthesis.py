"""
Synthesis section — collision of creative + analytical words with working memory titles.
"""

import random
from db import get_conn, WORKING_DB

SYMBOLS = ['→', '↔', '×', '⊕', '~', '⇌']


def pull_synthesis(creative_text, analytical_text):
    """Generate collisions between stream words and working memory titles."""
    # Gather input seeds
    input_seeds = []
    for text in [creative_text, analytical_text]:
        for word in text.lower().split():
            if word not in input_seeds:
                input_seeds.append(word)

    if not input_seeds:
        return None

    # Gather working memory seeds (topic titles + note titles)
    working_seeds = _get_working_seeds()
    if not working_seeds:
        return None

    # Generate 3 collisions: one input seed × one working seed
    collisions = []
    used_pairs = set()

    attempts = 0
    while len(collisions) < 3 and attempts < 20:
        attempts += 1
        left = random.choice(input_seeds)
        right = random.choice(working_seeds)
        pair = (left, right)

        if pair not in used_pairs:
            used_pairs.add(pair)
            sym = random.choice(SYMBOLS)
            collisions.append(f"  {left} {sym} {right}")

    return collisions if collisions else None


def _get_working_seeds():
    """Pull all topic titles and note titles from working memory."""
    try:
        conn = get_conn(WORKING_DB)
    except Exception:
        return []

    seeds = []

    # Topic titles
    rows = conn.execute('SELECT title FROM topics').fetchall()
    for r in rows:
        seeds.append(r['title'])

    # Note titles
    rows = conn.execute('SELECT title FROM notes').fetchall()
    for r in rows:
        seeds.append(r['title'])

    conn.close()
    return seeds
