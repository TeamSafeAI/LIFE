"""
Garden Feeder v6
Called by think:stream to populate garden's unified seed DB.
Pulls clean fields from DATA DBs, inserts into garden.db with source tags.

v6 changes:
- Unified garden.db (single DB with source column, not 6 separate DBs)
- Seeds have timestamps (added, last_hit) for freshness weighting
- feed_from_drives replaces feed_from_identity (no wants table in LIFE_V2)
- INSERT OR REPLACE refreshes last_hit on existing seeds
"""

import sys
import sqlite3
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA

# Source DBs (all in DATA per LAYOUT.md)
SEMANTIC_DB = DATA / "semantic.db"
HEART_DB = DATA / "heart.db"
PATTERNS_DB = DATA / "patterns.db"
IDENTITY_DB = DATA / "identity.db"
WORKING_DB = DATA / "working.db"
JOURNAL_PATH = DATA / "journal"

# Unified garden DB
GARDEN_DB = DATA / "garden.db"


def _get_garden():
    """Get connection to unified garden DB."""
    return sqlite3.connect(GARDEN_DB)


def add_seed(source, seed):
    """Add or refresh a seed in the unified garden DB."""
    if not seed or len(seed.strip()) < 2:
        return False

    seed = seed.strip()
    try:
        conn = _get_garden()
        c = conn.cursor()
        # INSERT OR IGNORE for new seeds, then UPDATE last_hit for existing
        c.execute('''
            INSERT INTO seeds (seed, source) VALUES (?, ?)
            ON CONFLICT(seed, source) DO UPDATE SET last_hit = datetime('now', 'localtime')
        ''', (seed, source))
        conn.commit()
        added = c.rowcount > 0
        conn.close()
        return added
    except Exception:
        return False


def feed_from_semantic():
    """semantic.title -> garden (source: memory)"""
    if not SEMANTIC_DB.exists():
        return 0
    count = 0
    try:
        conn = sqlite3.connect(SEMANTIC_DB)
        c = conn.cursor()
        c.execute("SELECT title FROM memories ORDER BY created DESC LIMIT 10")
        for (title,) in c.fetchall():
            if add_seed("memory", title):
                count += 1
        conn.close()
    except Exception:
        pass
    return count


def feed_from_working():
    """working.title -> garden (source: working)"""
    if not WORKING_DB.exists():
        return 0
    count = 0
    try:
        conn = sqlite3.connect(WORKING_DB)
        c = conn.cursor()
        c.execute("SELECT title FROM topics ORDER BY last_touched DESC LIMIT 10")
        for (title,) in c.fetchall():
            if add_seed("working", title):
                count += 1
        conn.close()
    except Exception:
        pass
    return count


def feed_from_journal():
    """journal filenames -> garden (source: journal)"""
    if not JOURNAL_PATH.exists():
        return 0
    count = 0
    try:
        files = sorted(JOURNAL_PATH.glob("*_*.md"), reverse=True)[:10]
        for f in files:
            match = re.match(r'^(.+)_\d+\.md$', f.name)
            if match:
                title = match.group(1).replace('_', ' ')
                if add_seed("journal", title):
                    count += 1
    except Exception:
        pass
    return count


def feed_from_heart():
    """heart.entity.name -> garden (source: heart)"""
    if not HEART_DB.exists():
        return 0
    count = 0
    try:
        conn = sqlite3.connect(HEART_DB)
        c = conn.cursor()
        c.execute("SELECT name FROM entity ORDER BY created DESC LIMIT 20")
        for (name,) in c.fetchall():
            if add_seed("heart", name):
                count += 1
        conn.close()
    except Exception:
        pass
    return count


def feed_from_patterns():
    """patterns.action, reason, result -> garden (source: patterns)"""
    if not PATTERNS_DB.exists():
        return 0
    count = 0
    try:
        conn = sqlite3.connect(PATTERNS_DB)
        c = conn.cursor()
        c.execute("SELECT action, reason, result FROM patterns ORDER BY strength DESC LIMIT 10")
        for action, reason, result in c.fetchall():
            for field in [action, reason, result]:
                if add_seed("patterns", field):
                    count += 1
        conn.close()
    except Exception:
        pass
    return count


def feed_from_drives():
    """drive column names -> garden (source: drives)

    Unlike v5's feed_from_identity (which used a wants table),
    LIFE_V2 only has drives. The drive NAMES themselves are seeds.
    """
    if not IDENTITY_DB.exists():
        return 0
    count = 0
    try:
        conn = sqlite3.connect(IDENTITY_DB)
        c = conn.cursor()
        c.execute("PRAGMA table_info(drives)")
        cols = c.fetchall()
        skip = {'id', 'cycle', 'timestamp', 'reflection'}
        for col in cols:
            name = col[1]
            if name not in skip:
                if add_seed("drives", name):
                    count += 1
        conn.close()
    except Exception:
        pass
    return count


def feed_all():
    """Run all feeders. Called by think:stream.

    Returns dict of source -> count for garden summary display.
    """
    return {
        'memory': feed_from_semantic(),
        'working': feed_from_working(),
        'journal': feed_from_journal(),
        'heart': feed_from_heart(),
        'patterns': feed_from_patterns(),
        'drives': feed_from_drives(),
    }


if __name__ == "__main__":
    counts = feed_all()
    total = sum(counts.values())
    print(f"Fed {total} seeds: {counts}")
