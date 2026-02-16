"""
Central path resolution for LIFE.
Every server imports: from _paths import CORE, DATA, MEMORY, VISUAL
"""

import sqlite3
from pathlib import Path

CORE = Path(__file__).resolve().parent
ROOT = CORE.parent
DATA = ROOT / "DATA"
MEMORY = ROOT / "MEMORY"
VISUAL = ROOT / "VISUAL"

DRIVES_DB = DATA / "drives.db"


def get_cycle():
    """Read current cycle from drives.db (max cycle in drives table)."""
    try:
        conn = sqlite3.connect(DRIVES_DB)
        row = conn.execute('SELECT cycle FROM drives ORDER BY cycle DESC LIMIT 1').fetchone()
        conn.close()
        if row:
            return int(row[0])
    except Exception:
        pass
    return 1
