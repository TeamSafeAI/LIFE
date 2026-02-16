"""
Shared DB connection and constants for working memory.
"""

import sqlite3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA, get_cycle

DB = DATA / 'working.db'


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def temperature(cycle, current):
    """Derive temperature from cycle difference."""
    diff = current - cycle
    if diff <= 5:
        return 'HOT'
    elif diff <= 15:
        return 'WARM'
    else:
        return 'COLD'


