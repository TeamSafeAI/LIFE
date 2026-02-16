"""
Shared DB connection for think.
"""

import sqlite3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA, get_cycle

DB = DATA / 'think.db'
HEART_DB = DATA / 'heart.db'
PATTERNS_DB = DATA / 'patterns.db'
SEMANTIC_DB = DATA / 'semantic.db'
WORKING_DB = DATA / 'working.db'

STREAMS = ['meta', 'cognitive', 'analytical', 'creative', 'relational', 'predictive']


def get_conn(db_path=None):
    conn = sqlite3.connect(db_path or DB)
    conn.row_factory = sqlite3.Row
    return conn


