"""
Week generator — compressed overview across a cycle range.
Counts + titles grouped by module, no per-cycle breakdown.
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
THINK_DB = DATA / 'think.db'
JOURNAL_DIR = DATA / 'journal'


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


def generate_week(lookback=15):
    """Build week summary — aggregated across last N cycles."""
    current = get_cycle()
    min_cycle = max(1, current - lookback + 1)

    sections = []

    # Memories — grouped by category
    rows = _safe_query(SEMANTIC_DB,
        'SELECT title, category FROM memories WHERE cycle BETWEEN ? AND ? ORDER BY id DESC',
        (min_cycle, current))
    if rows:
        by_cat = defaultdict(list)
        for r in rows:
            by_cat[r['category']].append(r['title'])
        sections.append(f"Memories: {len(rows)} stored")
        for cat, titles in by_cat.items():
            title_list = ', '.join(titles)
            sections.append(f"  {cat} ({len(titles)}): {title_list}")

    # Heart — unique entities with most recent notes
    rows = _safe_query(HEART_DB,
        'SELECT entity, notes, type FROM heart WHERE cycle BETWEEN ? AND ? ORDER BY id DESC',
        (min_cycle, current))
    if rows:
        entities = {}
        counts = defaultdict(int)
        for r in rows:
            counts[r['entity']] += 1
            if r['entity'] not in entities:
                entities[r['entity']] = (r['notes'], r['type'])
        sections.append(f"\nHeart: {len(entities)} entities touched")
        for entity, (notes, etype) in entities.items():
            sections.append(f"  {entity} — {counts[entity]} snapshots (latest: {notes})")

    # Patterns — count + most recent
    rows = _safe_query(PATTERNS_DB,
        'SELECT action, reason, result, lesson FROM patterns WHERE cycle BETWEEN ? AND ? ORDER BY id DESC',
        (min_cycle, current))
    if rows:
        sections.append(f"\nPatterns: {len(rows)} learned")
        r = rows[0]
        sections.append(f"  Most recent: {r['action']} → {r['reason']} → {r['result']} → {r['lesson']}")

    # Working threads — title, note count, temperature
    rows = _safe_query(WORKING_DB,
        'SELECT id, title, last_touched_cycle FROM topics ORDER BY last_touched_cycle DESC')
    if rows:
        sections.append(f"\nThreads: {len(rows)}")
        for r in rows:
            note_count = _safe_query(WORKING_DB,
                'SELECT COUNT(*) as cnt FROM notes WHERE thread_id = ?', (r['id'],))
            cnt = note_count[0]['cnt'] if note_count else 0
            diff = current - r['last_touched_cycle']
            if diff <= 5:
                temp = 'HOT'
            elif diff <= 15:
                temp = 'WARM'
            else:
                temp = 'COLD'
            sections.append(f"  {r['title']} ({cnt} notes, {temp})")

    # Journal — titles listed
    if JOURNAL_DIR.exists():
        entries = []
        for f in JOURNAL_DIR.glob('*.md'):
            parts = f.stem.rsplit('_', 2)
            if len(parts) == 3:
                try:
                    title, cycle, eid = parts[0], int(parts[1]), int(parts[2])
                    if min_cycle <= cycle <= current:
                        entries.append((eid, title))
                except ValueError:
                    pass
        entries.sort(key=lambda x: x[0], reverse=True)
        if entries:
            title_list = ', '.join(t for _, t in entries)
            sections.append(f"\nJournal: {len(entries)} entries")
            sections.append(f"  {title_list}")

    # Think — just count
    rows = _safe_query(THINK_DB,
        'SELECT COUNT(*) as cnt FROM thoughts WHERE cycle BETWEEN ? AND ?',
        (min_cycle, current))
    if rows and rows[0]['cnt'] > 0:
        sections.append(f"\nThink: {rows[0]['cnt']} captures")

    if not sections:
        return "No activity in range."

    return f"Week (Cycles {min_cycle}-{current}):\n\n" + '\n'.join(sections)
