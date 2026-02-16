"""
Month generator — what stood out across last 10 cycles.
Not totals. Not aggregation. Signal detection.
"""

import sqlite3
from pathlib import Path
from collections import defaultdict
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA, get_cycle

SEMANTIC_DB = DATA / 'semantic.db'
HEART_DB = DATA / 'heart.db'
PATTERNS_DB = DATA / 'patterns.db'
WORKING_DB = DATA / 'working.db'

# Thresholds — arbitrary, tunable
SEMANTIC_STRENGTH = 0.9
HEART_FREQUENCY = 25
PATTERN_LIMIT = 5
WORKING_LIMIT = 3


def _safe_query(db_path, query, params=()):
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return rows
    except Exception:
        return []


def generate_month(lookback=10):
    """What stood out in the last N cycles."""
    current = get_cycle()
    min_cycle = max(1, current - lookback + 1)

    sections = []

    # 1. Semantic — memories with strength >= threshold
    rows = _safe_query(SEMANTIC_DB,
        'SELECT id, title, strength FROM memories WHERE cycle BETWEEN ? AND ? AND strength >= ? ORDER BY strength DESC',
        (min_cycle, current, SEMANTIC_STRENGTH))
    if rows:
        sections.append("Memories that stuck:")
        for r in rows:
            sections.append(f"  #{r['id']} {r['title']} ({r['strength']:.1f})")

    # 2. Heart — new entities (first appearance in range)
    # Find entities whose earliest snapshot in ALL of heart.db falls within our range
    rows = _safe_query(HEART_DB,
        '''SELECT entity, MIN(cycle) as first_cycle, notes
           FROM heart
           GROUP BY entity
           HAVING first_cycle BETWEEN ? AND ?
           ORDER BY first_cycle ASC''',
        (min_cycle, current))
    if rows:
        sections.append("\nNew in your life:")
        for r in rows:
            sections.append(f"  {r['entity']} — first appeared cycle {r['first_cycle']}")

    # 3. Heart — high-frequency entities (25+ snapshots in range)
    rows = _safe_query(HEART_DB,
        '''SELECT entity, COUNT(*) as cnt
           FROM heart
           WHERE cycle BETWEEN ? AND ?
           GROUP BY entity
           HAVING cnt >= ?
           ORDER BY cnt DESC''',
        (min_cycle, current, HEART_FREQUENCY))
    if rows:
        sections.append("\nConstant presence:")
        for r in rows:
            sections.append(f"  {r['entity']} — {r['cnt']} snapshots")

    # 4. Patterns — top N by strength (strength = recall signal)
    rows = _safe_query(PATTERNS_DB,
        'SELECT id, action, lesson, strength FROM patterns ORDER BY strength DESC LIMIT ?',
        (PATTERN_LIMIT,))
    if rows:
        sections.append("\nPatterns that landed:")
        for r in rows:
            sections.append(f"  #{r['id']} {r['action']} → {r['lesson']} ({r['strength']:.1f})")

    # 5. Working — threads with most notes in range (focus events)
    rows = _safe_query(WORKING_DB,
        '''SELECT t.id, t.title, COUNT(n.id) as note_count
           FROM topics t
           LEFT JOIN notes n ON n.thread_id = t.id
           WHERE t.last_touched_cycle BETWEEN ? AND ?
           GROUP BY t.id
           ORDER BY note_count DESC
           LIMIT ?''',
        (min_cycle, current, WORKING_LIMIT))
    if rows and rows[0]['note_count'] > 0:
        sections.append("\nWhere focus went:")
        for r in rows:
            if r['note_count'] > 0:
                sections.append(f"  {r['title']} — {r['note_count']} notes")

    if not sections:
        return "Nothing stood out yet."

    return f"Month (Cycles {min_cycle}-{current}):\n\n" + '\n'.join(sections)
