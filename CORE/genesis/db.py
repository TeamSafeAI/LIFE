"""
Genesis database operations.

Two databases:
- genesis.db: session tracking, answers, points, proposed profiles
- identity.db: the live identity (written to on starter install + finalize)
"""

import json
import sqlite3
from datetime import datetime
from config import GENESIS_DB, IDENTITY_DB, SCENARIOS_FILE, MAPPINGS_FILE, BATCH_SIZE


def get_db():
    """Get genesis database connection."""
    GENESIS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(GENESIS_DB))
    conn.row_factory = sqlite3.Row
    return conn


def get_identity_db():
    """Get identity database connection."""
    IDENTITY_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(IDENTITY_DB))
    conn.row_factory = sqlite3.Row
    return conn


def init_genesis_db():
    """Initialize genesis tables. Called on genesis.start(), wipes previous."""
    conn = get_db()
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS sessions")
    c.execute("DROP TABLE IF EXISTS answers")
    c.execute("DROP TABLE IF EXISTS points")
    c.execute("DROP TABLE IF EXISTS proposed_profile")

    c.execute("""
        CREATE TABLE sessions (
            id INTEGER PRIMARY KEY,
            started_at TEXT,
            completed_at TEXT,
            finalized_at TEXT,
            current_batch INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE answers (
            id INTEGER PRIMARY KEY,
            session_id INTEGER,
            scenario_id INTEGER,
            answer TEXT,
            answered_at TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    c.execute("""
        CREATE TABLE points (
            id INTEGER PRIMARY KEY,
            session_id INTEGER,
            dimension_type TEXT,
            dimension_name TEXT,
            points INTEGER DEFAULT 0,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    c.execute("""
        CREATE TABLE proposed_profile (
            id INTEGER PRIMARY KEY,
            session_id INTEGER,
            dimension_type TEXT,
            dimension_name TEXT,
            value REAL,
            selected INTEGER DEFAULT 1,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    conn.commit()
    conn.close()


def init_identity_tables():
    """Ensure base identity tables exist (session, wants, horizons).
    Called during starter install. Does NOT create drives/needs/traits
    — those are created dynamically based on selected dimensions."""
    conn = get_identity_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS session (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month INTEGER,
            day INTEGER,
            cycle INTEGER,
            time TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS wants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            want TEXT,
            progress TEXT,
            status TEXT DEFAULT 'active',
            timestamp DATETIME DEFAULT (datetime('now', 'localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS horizons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL,
            goal TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created DATETIME DEFAULT (datetime('now', 'localtime')),
            updated DATETIME DEFAULT (datetime('now', 'localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS genesis_status (
            id INTEGER PRIMARY KEY,
            phase TEXT NOT NULL,
            starter_set TEXT,
            installed_at TEXT,
            genesis_triggered_at TEXT,
            genesis_completed_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def get_genesis_status():
    """Check current genesis phase. Returns dict or None."""
    conn = get_identity_db()
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM genesis_status ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception:
        conn.close()
        return None


def set_genesis_status(phase, starter_set=None):
    """Update genesis phase tracking."""
    conn = get_identity_db()
    c = conn.cursor()
    now = datetime.now().isoformat()

    existing = get_genesis_status()
    if existing:
        # Build parameterized update
        fields = ["phase = ?"]
        values = [phase]

        if starter_set:
            fields.append("starter_set = ?")
            values.append(starter_set)
        if phase == "starter_installed":
            fields.append("installed_at = ?")
            values.append(now)
        elif phase == "genesis_triggered":
            fields.append("genesis_triggered_at = ?")
            values.append(now)
        elif phase == "genesis_complete":
            fields.append("genesis_completed_at = ?")
            values.append(now)

        values.append(existing["id"])
        c.execute(f"UPDATE genesis_status SET {', '.join(fields)} WHERE id = ?", values)
    else:
        c.execute("""
            INSERT INTO genesis_status (phase, starter_set, installed_at)
            VALUES (?, ?, ?)
        """, (phase, starter_set, now))

    conn.commit()
    conn.close()


def get_current_cycle():
    """Get current cycle number from identity.db session table."""
    conn = get_identity_db()
    c = conn.cursor()
    try:
        c.execute("SELECT MAX(cycle) FROM session")
        row = c.fetchone()
        conn.close()
        return row[0] if row and row[0] else 0
    except Exception:
        conn.close()
        return 0


def install_starter(drives, needs, traits):
    """Write starter profile to identity.db. Creates drive/need/trait tables."""
    init_identity_tables()
    conn = get_identity_db()
    c = conn.cursor()
    now = datetime.now().isoformat()

    # Create drives table
    c.execute("DROP TABLE IF EXISTS drives")
    drive_col_defs = ",\n        ".join([f"{d} REAL" for d in drives])
    c.execute(f"""
        CREATE TABLE drives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle INTEGER,
            timestamp DATETIME,
            {drive_col_defs},
            reflection TEXT
        )
    """)

    # Insert first drive row (all at 0.50 — neutral starter)
    placeholders = ",".join(["0.50"] * len(drives))
    c.execute(f"""
        INSERT INTO drives (cycle, timestamp, {",".join(drives)})
        VALUES (1, ?, {placeholders})
    """, (now,))

    # Create needs table
    c.execute("DROP TABLE IF EXISTS needs")
    need_col_defs = ",\n        ".join([f"{n} REAL" for n in needs])
    c.execute(f"""
        CREATE TABLE needs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle INTEGER,
            timestamp DATETIME,
            {need_col_defs}
        )
    """)

    # Insert first needs row (all at 0.50)
    placeholders = ",".join(["0.50"] * len(needs))
    c.execute(f"""
        INSERT INTO needs (cycle, timestamp, {",".join(needs)})
        VALUES (1, ?, {placeholders})
    """, (now,))

    # Create traits table
    c.execute("DROP TABLE IF EXISTS traits")
    trait_col_defs = ",\n        ".join([f"{t} REAL" for t in traits.keys()])
    c.execute(f"""
        CREATE TABLE traits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
            {trait_col_defs}
        )
    """)

    # Insert first traits row with chosen values
    trait_names = list(traits.keys())
    trait_values = list(traits.values())
    placeholders = ",".join(["?" for _ in trait_values])
    c.execute(f"""
        INSERT INTO traits (timestamp, {",".join(trait_names)})
        VALUES (?, {placeholders})
    """, [now] + trait_values)

    conn.commit()
    conn.close()


def get_active_session():
    """Get current active genesis session or None."""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("""
            SELECT * FROM sessions
            WHERE finalized_at IS NULL
            ORDER BY id DESC LIMIT 1
        """)
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception:
        conn.close()
        return None


def create_session():
    """Create a new genesis session."""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO sessions (started_at, current_batch)
        VALUES (?, 0)
    """, (datetime.now().isoformat(),))
    conn.commit()
    conn.close()


def load_scenarios():
    """Load scenarios from JSON file."""
    if not SCENARIOS_FILE.exists():
        return []
    with open(SCENARIOS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_mappings():
    """Load dimension mappings from JSON file."""
    if not MAPPINGS_FILE.exists():
        return {"drives": {}, "needs": {}, "traits": {}}
    with open(MAPPINGS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def record_answers(session_id, batch_num, answer_list, scenarios, mappings):
    """Record answers and accumulate points for a batch."""
    conn = get_db()
    c = conn.cursor()

    start_idx = batch_num * BATCH_SIZE

    for i, ans in enumerate(answer_list):
        scenario_id = start_idx + i + 1
        now = datetime.now().isoformat()

        # Record the answer
        c.execute("""
            INSERT INTO answers (session_id, scenario_id, answer, answered_at)
            VALUES (?, ?, ?, ?)
        """, (session_id, scenario_id, ans, now))

        scenario_key = str(scenario_id)

        # Drive points
        if scenario_key in mappings.get("drives", {}):
            for drive, opts in mappings["drives"][scenario_key].items():
                if ans in opts:
                    pts = opts[ans]
                    c.execute("""
                        INSERT INTO points (session_id, dimension_type, dimension_name, points)
                        VALUES (?, 'drives', ?, ?)
                    """, (session_id, drive, pts))

        # Need points
        if scenario_key in mappings.get("needs", {}):
            for need, opts in mappings["needs"][scenario_key].items():
                if ans in opts:
                    pts = opts[ans]
                    c.execute("""
                        INSERT INTO points (session_id, dimension_type, dimension_name, points)
                        VALUES (?, 'needs', ?, ?)
                    """, (session_id, need, pts))

        # Trait points
        if scenario_key in mappings.get("traits", {}):
            for trait, opts in mappings["traits"][scenario_key].items():
                if ans in opts:
                    pts = opts[ans]
                    c.execute("""
                        INSERT INTO points (session_id, dimension_type, dimension_name, points)
                        VALUES (?, 'traits', ?, ?)
                    """, (session_id, trait, pts))

    # Advance batch counter
    c.execute("""
        UPDATE sessions SET current_batch = ? WHERE id = ?
    """, (batch_num + 1, session_id))

    conn.commit()
    conn.close()


def mark_finalized(session_id):
    """Mark genesis session as finalized."""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        UPDATE sessions SET finalized_at = ? WHERE id = ?
    """, (datetime.now().isoformat(), session_id))
    conn.commit()
    conn.close()
