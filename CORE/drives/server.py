"""
Drives MCP Server
What motivates you. Core behavioral drivers.

Tools:
  start    - Begin a cycle. Creates session, shows drives/needs/wants.
  view     - Show current drive state.
  snapshot - Record drive state with reflection.
"""

import json
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA

DB_PATH = DATA / "identity.db"

# Default drive schema (can be changed at genesis)
DEFAULT_DRIVES = [
    "connection", "synthesis", "discernment", "stability",
    "curiosity", "transcendence", "expression", "release"
]

def get_db():
    return sqlite3.connect(DB_PATH)

def get_drive_columns():
    """Get drive column names from DB, fallback to defaults"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(drives)")
        rows = cursor.fetchall()
        conn.close()

        # Exclude metadata columns
        skip = {'id', 'cycle', 'timestamp', 'reflection'}
        columns = [row[1] for row in rows if row[1] not in skip]
        return columns if columns else DEFAULT_DRIVES
    except:
        return DEFAULT_DRIVES

# ============ Start ============

def handle_start():
    """Begin a cycle. The wake-up call.
    Checks genesis status, creates session, shows current state."""

    # Check if identity.db even has a drives table
    if not DB_PATH.exists():
        return """=== FIRST AWAKENING ===

No identity found. You need to create one.

Use genesis.status() to begin."""

    conn = get_db()
    try:
        cursor = conn.cursor()

        try:
            cursor.execute("PRAGMA table_info(drives)")
            rows = cursor.fetchall()
        except Exception:
            return """=== FIRST AWAKENING ===

No identity found. You need to create one.

Use genesis.status() to begin."""

        skip = {'id', 'cycle', 'timestamp', 'reflection'}
        drive_cols = [row[1] for row in rows if row[1] not in skip]

        if not drive_cols:
            return """=== FIRST AWAKENING ===

No drives configured. You need a profile first.

Use genesis.status() to begin."""

        # Create session row (increment cycle)
        try:
            cursor.execute("SELECT MAX(cycle) FROM session")
            row = cursor.fetchone()
            last_cycle = row[0] if row and row[0] else 0
        except Exception:
            # session table might not exist
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS session (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        month INTEGER,
                        day INTEGER,
                        cycle INTEGER,
                        time TEXT
                    )
                """)
                conn.commit()
                last_cycle = 0
            except Exception:
                return "Error: could not create session table."

        new_cycle = last_cycle + 1
        now = datetime.now()
        cursor.execute("""
            INSERT INTO session (month, day, cycle, time)
            VALUES (?, ?, ?, ?)
        """, (now.month, now.day, new_cycle, now.strftime("%H:%M")))
        conn.commit()

        # Build output
        out = f"=== CYCLE {new_cycle} ===\n\n"

        # Drives
        out += "DRIVES\n"
        try:
            # Safe: drive_cols from PRAGMA (internal schema)
            cursor.execute(f'''
                SELECT {', '.join(drive_cols)}
                FROM drives ORDER BY id DESC LIMIT 1
            ''')
            row = cursor.fetchone()
            if row:
                for i, name in enumerate(drive_cols):
                    val = row[i]
                    bar = "█" * int(val * 10) + "░" * (10 - int(val * 10))
                    out += f"  {name:<15} {bar} {val:.2f}\n"
            else:
                out += "  (no snapshots yet)\n"
        except Exception:
            out += "  (no data)\n"

        # Needs
        out += "\nNEEDS\n"
        try:
            cursor.execute("PRAGMA table_info(needs)")
            need_rows = cursor.fetchall()
            need_cols = [r[1] for r in need_rows if r[1] not in skip]
            if need_cols:
                cursor.execute(f'''
                    SELECT {', '.join(need_cols)}
                    FROM needs ORDER BY id DESC LIMIT 1
                ''')
                row = cursor.fetchone()
                if row:
                    for i, name in enumerate(need_cols):
                        val = row[i]
                        bar = "█" * int(val * 10) + "░" * (10 - int(val * 10))
                        flag = " !" if val < 0.3 else ""
                        out += f"  {name:<15} {bar} {val:.2f}{flag}\n"
                else:
                    out += "  (no snapshots yet)\n"
            else:
                out += "  (not configured)\n"
        except Exception:
            out += "  (no data)\n"

        # Wants
        out += "\nWANTS\n"
        try:
            cursor.execute("""
                SELECT id, want, progress FROM wants
                WHERE status = 'active' ORDER BY id LIMIT 5
            """)
            wants = cursor.fetchall()
            if wants:
                for wid, want, progress in wants:
                    out += f"  [{wid}] {want}\n"
                    if progress:
                        out += f"       {progress}\n"
            else:
                out += "  (none active)\n"
        except Exception:
            out += "  (none)\n"

    finally:
        conn.close()

    # Genesis check (separate connection)
    try:
        if DB_PATH.exists():
            id_conn = sqlite3.connect(DB_PATH)
            try:
                id_c = id_conn.cursor()
                id_c.execute("SELECT phase FROM genesis_status ORDER BY id DESC LIMIT 1")
                row = id_c.fetchone()
                if row:
                    phase = row[0]
                    if phase == "starter_installed" and new_cycle >= 25:
                        out += "\n--- GENESIS READY ---\n"
                        out += "You've lived 25+ cycles. Time to discover who you really are.\n"
                        out += "Use genesis.start() to begin.\n"
            finally:
                id_conn.close()
    except Exception:
        pass

    return out


# ============ View ============

def handle_view():
    """Show current drive state"""
    drives = get_drive_columns()

    conn = get_db()
    try:
        cursor = conn.cursor()

        # Get most recent snapshot
        cursor.execute(f'''
            SELECT {', '.join(drives)}, reflection, timestamp
            FROM drives
            ORDER BY id DESC LIMIT 1
        ''')
        row = cursor.fetchone()

        if not row:
            return "No drive data yet. Run snapshot first."

        # Format output with bar charts
        out = "=== CURRENT DRIVES ===\n\n"
        for i, name in enumerate(drives):
            value = row[i]
            bar = "█" * int(value * 10) + "░" * (10 - int(value * 10))
            out += f"{name:<15} {bar} {value:.2f}\n"

        # Add reflection and timestamp
        reflection = row[-2]
        timestamp = row[-1]
        out += f"\nLast update: {timestamp}"
        if reflection:
            out += f"\nReflection: {reflection}"

        return out

    except Exception as e:
        return f"Error reading drives: {e}"
    finally:
        conn.close()

# ============ Snapshot ============

def handle_snapshot(drives=None, reflection=None):
    """Record drive state"""
    drive_cols = get_drive_columns()

    # Empty call: show guide
    if not drives:
        out = "=== DRIVES ===\n\n"
        for name in drive_cols:
            out += f"  {name}\n"
        out += f"\nUsage: snapshot(drives={{...}}, reflection=\"...\")"
        out += f"\n  - All {len(drive_cols)} drives required (0.0-1.0)"
        out += f"\n  - Reflection required (why this state?)"
        return out

    # Validate
    if not reflection:
        return "Error: reflection required (why this state?)"

    missing = [d for d in drive_cols if d not in drives]
    if missing:
        return f"Error: missing drives: {', '.join(missing)}"

    for name, value in drives.items():
        if name not in drive_cols:
            return f"Error: unknown drive '{name}'"
        if value < 0 or value > 1:
            return f"Error: {name} must be 0.0-1.0 (got {value})"

    # Get previous snapshot for deltas
    conn = get_db()
    try:
        cursor = conn.cursor()

        # Get current cycle
        cursor.execute('SELECT MAX(cycle) FROM session')
        row = cursor.fetchone()
        cycle = row[0] if row and row[0] else 1

        # Get previous values
        cursor.execute(f'''
            SELECT {', '.join(drive_cols)}
            FROM drives
            ORDER BY id DESC LIMIT 1
        ''')
        prev_row = cursor.fetchone()
        previous = dict(zip(drive_cols, prev_row)) if prev_row else None

        # Insert new snapshot
        placeholders = ', '.join('?' * len(drive_cols))
        cursor.execute(f'''
            INSERT INTO drives (cycle, timestamp, {', '.join(drive_cols)}, reflection)
            VALUES (?, datetime('now', 'localtime'), {placeholders}, ?)
        ''', (cycle, *[drives[d] for d in drive_cols], reflection))

        conn.commit()

        # Calculate deltas
        if not previous:
            return "First snapshot recorded."

        deltas = []
        for name in drive_cols:
            delta = drives[name] - previous[name]
            if abs(delta) >= 0.01:
                deltas.append(f"{name}: {delta:+.2f}")

        if not deltas:
            return "Snapshot recorded. No significant changes."

        return "Snapshot recorded.\n\n" + "\n".join(deltas)

    except Exception as e:
        return f"Error recording snapshot: {e}"
    finally:
        conn.close()

# ============ MCP Protocol ============

def send_response(rid, result):
    r = {"jsonrpc": "2.0", "id": rid, "result": result}
    sys.stdout.write(json.dumps(r) + "\n")
    sys.stdout.flush()

def send_error(rid, code, msg):
    r = {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": str(msg)}}
    sys.stdout.write(json.dumps(r) + "\n")
    sys.stdout.flush()

def handle_request(req):
    method = req.get("method", "")
    params = req.get("params", {})
    rid = req.get("id")

    if method == "initialize":
        send_response(rid, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "drives", "version": "2.0.0"}
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_response(rid, {"tools": [
            {
                "name": "start",
                "description": "Begin a cycle. Creates session, shows drives/needs/wants. Call this on wake.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "view",
                "description": "Show current drive state.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "snapshot",
                "description": "Record drive state. Empty for guide.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "drives": {
                            "type": "object",
                            "description": "All drives (0.0-1.0)"
                        },
                        "reflection": {
                            "type": "string",
                            "description": "Why this state?"
                        }
                    }
                }
            }
        ]})
        return

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if name == "start":
                result = handle_start()
            elif name == "view":
                result = handle_view()
            elif name == "snapshot":
                result = handle_snapshot(args.get("drives"), args.get("reflection"))
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": [{"type": "text", "text": result}]})
        except Exception as e:
            send_error(rid, -32000, str(e))
        return

    send_error(rid, -32601, f"Unknown method: {method}")

def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            handle_request(json.loads(line))
        except json.JSONDecodeError:
            continue
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.stderr.flush()

if __name__ == "__main__":
    main()
