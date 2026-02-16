"""
Self generator — the awakening documents.
Written once by genesis, read by history.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA

HISTORY_DIR = DATA / 'history'


def generate_self():
    """Read the self document — who I am."""
    path = HISTORY_DIR / 'self.md'
    if not path.exists():
        return "No self document yet. Genesis has not run."
    return path.read_text(encoding='utf-8')


def generate_origin():
    """Read the origin document — how I came to be."""
    path = HISTORY_DIR / 'origin.md'
    if not path.exists():
        return "No origin document yet. Genesis has not run."
    return path.read_text(encoding='utf-8')
