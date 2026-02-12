"""
Forecast DB Schema
Table: forecasts
"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,
    reason TEXT NOT NULL,
    expected TEXT NOT NULL,
    action TEXT NOT NULL,
    created TEXT DEFAULT (datetime('now', 'localtime')),
    lesson TEXT,
    status TEXT DEFAULT 'active'
)
"""

# Status options: active, passed, failed, expired
