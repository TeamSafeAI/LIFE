"""
Central path resolution for LIFE_V2.
Every server imports from here: `from _paths import CORE, DATA`

Layout (from LAYOUT.md):
  LIFE_V2/
  ├── CORE/     MCP servers (this file lives here)
  ├── DATA/     SQLite databases (ALL .db files go here)
  ├── MEMORY/   File storage (journals, semantic content, history)
  ├── GUIDE/    Usage docs
  └── VISUAL/   Images
"""

from pathlib import Path

# CORE = directory where servers live (where this file is)
CORE = Path(__file__).resolve().parent

# Root = one level up from CORE
ROOT = CORE.parent

# DATA = where all .db files live
DATA = ROOT / "DATA"

# MEMORY = file storage (journals, semantic markdown, history)
MEMORY = ROOT / "MEMORY"

# VISUAL = images (vision captures, dashboards)
VISUAL = ROOT / "VISUAL"

# GUIDE = documentation
GUIDE = ROOT / "GUIDE"
