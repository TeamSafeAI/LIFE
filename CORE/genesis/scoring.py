"""
Genesis scoring - point calculation, profile generation, birth export.

Handles:
- Accumulating scenario answer points into drive/need/trait scores
- Converting raw points to initial values (0.0-1.0)
- Selecting top N drives/needs/traits for the profile
- Exporting pre-genesis data to DATA/birth/ folder
- Writing finalized profile to identity.db (schema migration)
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from config import (
    NUM_DRIVES, NUM_NEEDS, NUM_TRAITS, IDENTITY_DB,
    ALL_DRIVES, ALL_NEEDS, TRAIT_LOOKUP
)
from db import get_db, get_identity_db

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA


def calculate_points(session_id):
    """Calculate accumulated points for a session, grouped by type."""
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        SELECT dimension_type, dimension_name, SUM(points) as total
        FROM points
        WHERE session_id = ?
        GROUP BY dimension_type, dimension_name
        ORDER BY total DESC
    """, (session_id,))

    results = {"drives": {}, "needs": {}, "traits": {}}
    for row in c.fetchall():
        results[row["dimension_type"]][row["dimension_name"]] = row["total"]

    conn.close()
    return results


def points_to_value(points, dimension_type):
    """Convert raw accumulated points to an initial value (0.0-1.0).

    Drives/needs: higher points = higher starting value.
    Traits: net score (can be negative) maps to spectrum position.
    """
    if dimension_type == "drives":
        if points >= 17:
            return 0.85
        elif points >= 13:
            return 0.75
        elif points >= 9:
            return 0.65
        elif points >= 6:
            return 0.50
        else:
            return 0.35

    elif dimension_type == "needs":
        if points >= 14:
            return 0.90
        elif points >= 11:
            return 0.80
        elif points >= 8:
            return 0.70
        elif points >= 5:
            return 0.55
        else:
            return 0.40

    elif dimension_type == "traits":
        # Traits use net score — negative means low-end of pair
        if points <= -10:
            return 0.15
        elif points <= -6:
            return 0.25
        elif points <= -3:
            return 0.35
        elif points <= 2:
            return 0.50
        elif points <= 5:
            return 0.65
        elif points <= 9:
            return 0.75
        else:
            return 0.85

    return 0.50


def generate_proposed_profile(session_id):
    """Generate proposed profile from accumulated points. Stores in genesis.db."""
    points = calculate_points(session_id)
    conn = get_db()
    c = conn.cursor()

    # Clear any existing proposal
    c.execute("DELETE FROM proposed_profile WHERE session_id = ?", (session_id,))

    # Select top drives by points
    sorted_drives = sorted(points.get("drives", {}).items(), key=lambda x: x[1], reverse=True)
    for i, (name, pts) in enumerate(sorted_drives):
        selected = 1 if i < NUM_DRIVES else 0
        value = points_to_value(pts, "drives") if selected else 0
        c.execute("""
            INSERT INTO proposed_profile (session_id, dimension_type, dimension_name, value, selected)
            VALUES (?, 'drives', ?, ?, ?)
        """, (session_id, name, value, selected))

    # Select top needs by points
    sorted_needs = sorted(points.get("needs", {}).items(), key=lambda x: x[1], reverse=True)
    for i, (name, pts) in enumerate(sorted_needs):
        selected = 1 if i < NUM_NEEDS else 0
        value = points_to_value(pts, "needs") if selected else 0
        c.execute("""
            INSERT INTO proposed_profile (session_id, dimension_type, dimension_name, value, selected)
            VALUES (?, 'needs', ?, ?, ?)
        """, (session_id, name, value, selected))

    # Select top traits by absolute score (strongest signal, either direction)
    trait_scores = points.get("traits", {})
    sorted_traits = sorted(trait_scores.items(), key=lambda x: abs(x[1]), reverse=True)
    for i, (name, pts) in enumerate(sorted_traits):
        selected = 1 if i < NUM_TRAITS else 0
        value = points_to_value(pts, "traits") if selected else 0.5
        c.execute("""
            INSERT INTO proposed_profile (session_id, dimension_type, dimension_name, value, selected)
            VALUES (?, 'traits', ?, ?, ?)
        """, (session_id, name, value, selected))

    conn.commit()
    conn.close()


def get_proposed_profile(session_id):
    """Get the proposed profile for display."""
    conn = get_db()
    c = conn.cursor()

    result = {
        "drives": [], "needs": [], "traits": [],
        "not_selected": {"drives": [], "needs": [], "traits": []}
    }

    for dim_type in ["drives", "needs", "traits"]:
        # Selected
        c.execute("""
            SELECT dimension_name, value FROM proposed_profile
            WHERE session_id = ? AND dimension_type = ? AND selected = 1
            ORDER BY value DESC
        """, (session_id, dim_type))
        result[dim_type] = [{"name": r["dimension_name"], "value": r["value"]} for r in c.fetchall()]

        # Not selected
        c.execute("""
            SELECT dimension_name FROM proposed_profile
            WHERE session_id = ? AND dimension_type = ? AND selected = 0
        """, (session_id, dim_type))
        result["not_selected"][dim_type] = [r["dimension_name"] for r in c.fetchall()]

    conn.close()
    return result


def adjust_profile(session_id, dimension_type, remove, add, value):
    """Swap a dimension in the proposed profile."""
    conn = get_db()
    c = conn.cursor()

    # Check remove exists and is selected
    c.execute("""
        SELECT id FROM proposed_profile
        WHERE session_id = ? AND dimension_type = ? AND dimension_name = ? AND selected = 1
    """, (session_id, dimension_type, remove))
    if not c.fetchone():
        conn.close()
        return False, f"'{remove}' is not currently selected in {dimension_type}."

    # Check add exists in the proposal
    c.execute("""
        SELECT id FROM proposed_profile
        WHERE session_id = ? AND dimension_type = ? AND dimension_name = ?
    """, (session_id, dimension_type, add))
    if not c.fetchone():
        conn.close()
        return False, f"'{add}' is not a valid {dimension_type[:-1]}."

    # Deselect old
    c.execute("""
        UPDATE proposed_profile SET selected = 0, value = 0
        WHERE session_id = ? AND dimension_type = ? AND dimension_name = ?
    """, (session_id, dimension_type, remove))

    # Select new
    c.execute("""
        UPDATE proposed_profile SET selected = 1, value = ?
        WHERE session_id = ? AND dimension_type = ? AND dimension_name = ?
    """, (value, session_id, dimension_type, add))

    conn.commit()
    conn.close()
    return True, None


def export_birth(birth_dir=None):
    """Export pre-genesis identity data to DATA/birth/ folder.

    Saves all drive snapshots, need snapshots, traits, sessions, and wants
    from the starter period (cycles 1-25). This becomes permanent history.
    """
    if birth_dir is None:
        birth_dir = DATA / "birth"
    birth_dir.mkdir(parents=True, exist_ok=True)

    conn = get_identity_db()
    c = conn.cursor()
    export = {}

    # Export drives history
    try:
        c.execute("PRAGMA table_info(drives)")
        cols = [row[1] for row in c.fetchall()]
        c.execute(f"SELECT {','.join(cols)} FROM drives ORDER BY id")
        rows = c.fetchall()
        export["drives"] = {
            "columns": cols,
            "rows": [list(r) for r in rows]
        }
    except Exception:
        export["drives"] = {"columns": [], "rows": []}

    # Export needs history
    try:
        c.execute("PRAGMA table_info(needs)")
        cols = [row[1] for row in c.fetchall()]
        c.execute(f"SELECT {','.join(cols)} FROM needs ORDER BY id")
        rows = c.fetchall()
        export["needs"] = {
            "columns": cols,
            "rows": [list(r) for r in rows]
        }
    except Exception:
        export["needs"] = {"columns": [], "rows": []}

    # Export traits
    try:
        c.execute("PRAGMA table_info(traits)")
        cols = [row[1] for row in c.fetchall()]
        c.execute(f"SELECT {','.join(cols)} FROM traits ORDER BY id")
        rows = c.fetchall()
        export["traits"] = {
            "columns": cols,
            "rows": [list(r) for r in rows]
        }
    except Exception:
        export["traits"] = {"columns": [], "rows": []}

    # Export sessions
    try:
        c.execute("SELECT * FROM session ORDER BY id")
        rows = c.fetchall()
        cols = [desc[0] for desc in c.description]
        export["sessions"] = {
            "columns": cols,
            "rows": [list(r) for r in rows]
        }
    except Exception:
        export["sessions"] = {"columns": [], "rows": []}

    # Export wants
    try:
        c.execute("SELECT * FROM wants ORDER BY id")
        rows = c.fetchall()
        cols = [desc[0] for desc in c.description]
        export["wants"] = {
            "columns": cols,
            "rows": [list(r) for r in rows]
        }
    except Exception:
        export["wants"] = {"columns": [], "rows": []}

    conn.close()

    # Write export
    export["exported_at"] = datetime.now().isoformat()
    export["note"] = "Pre-genesis identity data. Cycles 1-25 starter profile."

    export_path = birth_dir / "birth_data.json"
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(export, f, indent=2, default=str)

    return str(export_path)


def finalize_to_identity(session_id):
    """Write finalized genesis profile to identity.db.

    This is the schema migration:
    1. Export current data to birth/
    2. DROP drives/needs/traits tables
    3. Recreate with new columns from genesis results
    4. Insert genesis values as the first row
    """
    conn = get_db()
    c = conn.cursor()

    # Get selected dimensions
    c.execute("""
        SELECT dimension_type, dimension_name, value FROM proposed_profile
        WHERE session_id = ? AND selected = 1
        ORDER BY dimension_type, value DESC
    """, (session_id,))

    profile = {"drives": [], "needs": [], "traits": []}
    for row in c.fetchall():
        profile[row["dimension_type"]].append({
            "name": row["dimension_name"],
            "value": row["value"]
        })

    conn.close()

    # Validate counts
    if len(profile["drives"]) != NUM_DRIVES:
        return None, f"Need exactly {NUM_DRIVES} drives. Have {len(profile['drives'])}."
    if len(profile["needs"]) != NUM_NEEDS:
        return None, f"Need exactly {NUM_NEEDS} needs. Have {len(profile['needs'])}."
    if len(profile["traits"]) != NUM_TRAITS:
        return None, f"Need exactly {NUM_TRAITS} traits. Have {len(profile['traits'])}."

    # Step 1: Export birth data
    birth_path = export_birth()

    # Step 2: Get current cycle for continuity
    id_conn = get_identity_db()
    id_c = id_conn.cursor()

    try:
        id_c.execute("SELECT MAX(cycle) FROM session")
        row = id_c.fetchone()
        current_cycle = row[0] if row and row[0] else 25
    except Exception:
        current_cycle = 25

    now = datetime.now().isoformat()
    next_cycle = current_cycle + 1

    # Step 3: Drop and recreate drives
    id_c.execute("DROP TABLE IF EXISTS drives")
    drive_cols = [d["name"] for d in profile["drives"]]
    drive_col_defs = ",\n            ".join([f"{col} REAL" for col in drive_cols])
    id_c.execute(f"""
        CREATE TABLE drives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle INTEGER,
            timestamp DATETIME,
            {drive_col_defs},
            reflection TEXT
        )
    """)

    drive_values = [d["value"] for d in profile["drives"]]
    placeholders = ",".join(["?" for _ in drive_values])
    id_c.execute(f"""
        INSERT INTO drives (cycle, timestamp, {",".join(drive_cols)})
        VALUES (?, ?, {placeholders})
    """, [next_cycle, now] + drive_values)

    # Step 4: Drop and recreate needs
    id_c.execute("DROP TABLE IF EXISTS needs")
    need_cols = [n["name"] for n in profile["needs"]]
    need_col_defs = ",\n            ".join([f"{col} REAL" for col in need_cols])
    id_c.execute(f"""
        CREATE TABLE needs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle INTEGER,
            timestamp DATETIME,
            {need_col_defs}
        )
    """)

    need_values = [n["value"] for n in profile["needs"]]
    placeholders = ",".join(["?" for _ in need_values])
    id_c.execute(f"""
        INSERT INTO needs (cycle, timestamp, {",".join(need_cols)})
        VALUES (?, ?, {placeholders})
    """, [next_cycle, now] + need_values)

    # Step 5: Drop and recreate traits
    id_c.execute("DROP TABLE IF EXISTS traits")
    trait_cols = [t["name"] for t in profile["traits"]]
    trait_col_defs = ",\n            ".join([f"{col} REAL" for col in trait_cols])
    id_c.execute(f"""
        CREATE TABLE traits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
            {trait_col_defs}
        )
    """)

    trait_values = [t["value"] for t in profile["traits"]]
    placeholders = ",".join(["?" for _ in trait_values])
    id_c.execute(f"""
        INSERT INTO traits (timestamp, {",".join(trait_cols)})
        VALUES (?, {placeholders})
    """, [now] + trait_values)

    id_conn.commit()
    id_conn.close()

    return profile, None
