"""
Day generator — recent actions across all modules.
What did I actually do? Pulled live from DBs, filtered by cycle.
"""

import sqlite3
from pathlib import Path
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
    """Query a DB, return rows or empty list if DB missing."""
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


def _journal_entries_for_cycles(cycles):
    """Parse journal filenames for entries in given cycle range."""
    if not JOURNAL_DIR.exists():
        return []

    results = []
    for f in JOURNAL_DIR.glob('*.md'):
        parts = f.stem.rsplit('_', 2)
        if len(parts) == 3:
            try:
                title, cycle, eid = parts[0], int(parts[1]), int(parts[2])
                if cycle in cycles:
                    results.append((eid, title, cycle))
            except ValueError:
                pass
    results.sort(key=lambda x: x[0], reverse=True)
    return results


def generate_day(lookback=3):
    """Build the day summary — actions from last N cycles."""
    current = get_cycle()
    min_cycle = current - lookback + 1
    cycle_range = set(range(min_cycle, current + 1))

    sections = []

    # Group by cycle, newest first
    for cycle in range(current, min_cycle - 1, -1):
        cycle_sections = []

        # Semantic
        rows = _safe_query(SEMANTIC_DB,
            'SELECT title, category FROM memories WHERE cycle = ? ORDER BY id DESC', (cycle,))
        for r in rows:
            cycle_sections.append(f"  Stored memory: {r['title']} [{r['category']}]")

        # Heart
        rows = _safe_query(HEART_DB,
            'SELECT entity, notes FROM heart WHERE cycle = ? ORDER BY id DESC', (cycle,))
        for r in rows:
            cycle_sections.append(f"  Felt: {r['entity']} — {r['notes']}")

        # Patterns
        rows = _safe_query(PATTERNS_DB,
            'SELECT action, reason, result, lesson FROM patterns WHERE cycle = ? ORDER BY id DESC', (cycle,))
        for r in rows:
            cycle_sections.append(f"  Learned: {r['action']} → {r['reason']} → {r['result']} → {r['lesson']}")

        # Working threads touched this cycle
        rows = _safe_query(WORKING_DB,
            'SELECT title FROM topics WHERE last_touched_cycle = ? ORDER BY id DESC', (cycle,))
        for r in rows:
            cycle_sections.append(f"  Thread active: {r['title']}")

        # Working notes added (no cycle on notes, so use thread touch cycle as proxy)
        rows = _safe_query(WORKING_DB,
            '''SELECT n.title, t.title as thread FROM notes n
               JOIN topics t ON n.thread_id = t.id
               WHERE t.last_touched_cycle = ?
               ORDER BY n.id DESC''', (cycle,))
        for r in rows:
            cycle_sections.append(f"  Added note: {r['title']} (to {r['thread']})")

        # Journal
        journal = [e for e in _journal_entries_for_cycles({cycle})]
        for eid, title, _ in journal:
            cycle_sections.append(f"  Journal: {title}")

        # Think — count for this cycle
        rows = _safe_query(THINK_DB,
            'SELECT COUNT(*) as cnt FROM thoughts WHERE cycle = ?', (cycle,))
        if rows and rows[0]['cnt'] > 0:
            cycle_sections.append(f"  Think: {rows[0]['cnt']} captures")

        if cycle_sections:
            sections.append(f"Cycle {cycle}:")
            sections.extend(cycle_sections)
            sections.append("")

    if not sections:
        return "No recent activity."

    return '\n'.join(sections).rstrip()
