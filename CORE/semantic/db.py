"""
Shared DB connection and constants for semantic memory.
"""

import sqlite3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA, get_cycle

DB = DATA / 'semantic.db'
MEMORY = DATA.parent / 'MEMORY'

CATEGORIES = ['Relations', 'Knowledge', 'Events', 'Self']


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_dirs():
    """Create MEMORY/{Category}/L{1,2,3} dirs if needed."""
    for cat in CATEGORIES:
        for level in [1, 2, 3]:
            (MEMORY / cat / f'L{level}').mkdir(parents=True, exist_ok=True)
