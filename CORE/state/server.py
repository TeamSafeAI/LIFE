"""
State MCP Server v3
Visual dashboard + horizon tracking.

Tools:
  view     - Generate state snapshot (PNG image)
  check    - Text summary of current state
  needs    - Record needs snapshot
  want     - Manage wants (add/update/archive)
  horizon  - Set short/medium/long term goals
"""

import json
import sys
import sqlite3
import base64
from datetime import datetime
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA, VISUAL

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

DB_PATH = DATA / "identity.db"
OUTPUT_PATH = VISUAL

DEFAULT_NEEDS = ["integrity", "connection", "clarity", "purpose", "autonomy"]

COLOR_PALETTE = [
    "#FF6B6B", "#4ECDC4", "#F7DC6F", "#BB8FCE", "#85C1E9",
    "#F8B500", "#45B7D1", "#F1948A", "#AAB7B8", "#F39C12",
    "#9B59B6", "#2ECC71", "#E74C3C", "#3498DB", "#1ABC9C"
]

_schema_cache = {}


def get_db():
    if not DB_PATH.exists():
        return None
    return sqlite3.connect(DB_PATH)


def init_tables():
    """Create wants and horizons tables if they don't exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS wants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            want TEXT NOT NULL,
            progress TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            timestamp DATETIME DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS horizons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL,
            goal TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created DATETIME DEFAULT (datetime('now', 'localtime')),
            updated DATETIME DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    conn.commit()
    conn.close()


def get_schema(table_name):
    """Get column names from a table, excluding metadata."""
    if table_name in _schema_cache:
        return _schema_cache[table_name]
    conn = get_db()
    if not conn:
        return []
    cursor = conn.cursor()
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        rows = cursor.fetchall()
    except Exception:
        conn.close()
        return []
    conn.close()
    skip = {'id', 'cycle', 'timestamp', 'reflection'}
    columns = [row[1] for row in rows if row[1] not in skip]
    _schema_cache[table_name] = columns
    return columns


def get_color(index):
    return COLOR_PALETTE[index % len(COLOR_PALETTE)]


# ============ Data Readers ============

def get_drives_latest():
    """Get most recent drive values."""
    drives = get_schema('drives')
    if not drives:
        return {}, []
    conn = get_db()
    if not conn:
        return {}, drives
    c = conn.cursor()
    try:
        c.execute(f'SELECT {", ".join(drives)} FROM drives ORDER BY id DESC LIMIT 1')
        row = c.fetchone()
        conn.close()
        if row:
            return dict(zip(drives, row)), drives
        return {}, drives
    except Exception:
        conn.close()
        return {}, drives


def get_drives_history(limit=50):
    drives = get_schema('drives')
    if not drives:
        return [], {}, []
    conn = get_db()
    if not conn:
        return [], {}, []
    c = conn.cursor()
    try:
        c.execute(f'''
            SELECT cycle, {', '.join(drives)} FROM drives
            ORDER BY id DESC LIMIT ?
        ''', (limit,))
        rows = list(reversed(c.fetchall()))
        conn.close()
        if not rows:
            return [], {}, drives
        labels = [f"C{r[0]}" for r in rows]
        data = {d: [r[i+1] for r in rows] for i, d in enumerate(drives)}
        return labels, data, drives
    except Exception:
        conn.close()
        return [], {}, drives


def get_needs_latest():
    """Get most recent needs values."""
    needs = get_schema('needs')
    if not needs:
        return {}, DEFAULT_NEEDS
    conn = get_db()
    if not conn:
        return {}, needs
    c = conn.cursor()
    try:
        c.execute(f'SELECT {", ".join(needs)} FROM needs ORDER BY id DESC LIMIT 1')
        row = c.fetchone()
        conn.close()
        if row:
            return dict(zip(needs, row)), needs
        return {}, needs
    except Exception:
        conn.close()
        return {}, needs


def get_wants():
    conn = get_db()
    if not conn:
        return []
    c = conn.cursor()
    try:
        c.execute("SELECT id, want, progress FROM wants WHERE status = 'active' ORDER BY id LIMIT 5")
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception:
        conn.close()
        return []


def get_horizons():
    """Get active horizons grouped by scope."""
    conn = get_db()
    if not conn:
        return {"short": [], "medium": [], "long": []}
    c = conn.cursor()
    try:
        c.execute('''
            SELECT scope, goal FROM horizons
            WHERE status = 'active'
            ORDER BY scope, id
        ''')
        rows = c.fetchall()
        conn.close()

        result = {"short": [], "medium": [], "long": []}
        for scope, goal in rows:
            if scope in result:
                result[scope].append(goal)
        return result
    except Exception:
        conn.close()
        return {"short": [], "medium": [], "long": []}


def get_current_session():
    conn = get_db()
    if not conn:
        return None
    c = conn.cursor()
    try:
        c.execute('SELECT cycle FROM session ORDER BY id DESC LIMIT 1')
        row = c.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception:
        conn.close()
        return None


# ============ Image Generation ============

def generate_image():
    """Generate the state snapshot PNG."""
    if not HAS_MPL:
        return None, "matplotlib not installed"

    drive_data, drive_names = get_drives_latest()
    drive_labels, drive_history, _ = get_drives_history(50)
    need_data, need_names = get_needs_latest()
    wants = get_wants()
    horizons = get_horizons()
    session = get_current_session()

    # 4-row layout: drives history | current drives + needs | horizons | status
    fig = plt.figure(figsize=(14, 12), facecolor='#0d1117')
    gs = GridSpec(4, 2, figure=fig, height_ratios=[1.8, 1.2, 1.5, 0.8],
                  hspace=0.35, wspace=0.25, left=0.06, right=0.94, top=0.93, bottom=0.04)

    # Title
    fig.suptitle('LIFE STATE', fontsize=16, color='#85C1E9', fontweight='bold', y=0.97)

    # === ROW 1: DRIVE HISTORY (full width) ===
    ax_hist = fig.add_subplot(gs[0, :])
    ax_hist.set_facecolor('#0d1117')
    ax_hist.set_title('DRIVES', fontsize=10, color='#FF6B6B', loc='left', pad=8)

    if drive_history and drive_names:
        x = range(len(drive_labels))
        for i, drive in enumerate(drive_names):
            color = get_color(i)
            vals = drive_history[drive]
            current = vals[-1] if vals else 0
            ax_hist.plot(x, vals, color=color, linewidth=1.5, alpha=0.9)
            ax_hist.scatter([len(vals)-1], [current], color=color, s=20, zorder=5)

        ax_hist.set_xlim(-0.5, len(drive_labels)-0.5)
        ax_hist.set_ylim(0, 1.05)
        step = max(1, len(drive_labels)//15)
        ax_hist.set_xticks(range(0, len(drive_labels), step))
        ax_hist.set_xticklabels([drive_labels[i] for i in range(0, len(drive_labels), step)],
                                 fontsize=7, color='#666', rotation=45)
        ax_hist.set_yticks([0, 0.5, 1.0])
        ax_hist.set_yticklabels(['0', '0.5', '1.0'], fontsize=8, color='#666')

        for i, d in enumerate(drive_names):
            color = get_color(i)
            val = drive_history[d][-1] if drive_history[d] else 0
            ax_hist.annotate(f"{d} {val:.2f}", xy=(1.01, 0.95 - i*0.08),
                            xycoords='axes fraction', fontsize=8, color=color, va='top')
    else:
        ax_hist.text(0.5, 0.5, 'No drive data', ha='center', va='center', color='#444', fontsize=12)
        ax_hist.set_xticks([])
        ax_hist.set_yticks([])

    for spine in ['top', 'right']:
        ax_hist.spines[spine].set_visible(False)
    for spine in ['bottom', 'left']:
        ax_hist.spines[spine].set_color('#333')
    ax_hist.tick_params(colors='#666')

    # === ROW 2 LEFT: NEEDS BARS ===
    ax_needs = fig.add_subplot(gs[1, 0])
    ax_needs.set_facecolor('#0d1117')
    ax_needs.set_title('NEEDS', fontsize=10, color='#4ECDC4', loc='left', pad=8)

    active_needs = need_names if need_names else DEFAULT_NEEDS
    if need_data:
        y_pos = range(len(active_needs))
        values = [need_data.get(n, 0) for n in active_needs]
        colors = ['#E74C3C' if v < 0.3 else '#F39C12' if v < 0.5 else '#4ECDC4' for v in values]
        ax_needs.barh(y_pos, values, color=colors, alpha=0.8, height=0.6)
        ax_needs.set_yticks(y_pos)
        ax_needs.set_yticklabels(active_needs, fontsize=8, color='#aaa')
        ax_needs.set_xlim(0, 1)
        ax_needs.set_xticks([0, 0.5, 1])
        ax_needs.set_xticklabels(['0', '0.5', '1.0'], fontsize=7, color='#666')
        ax_needs.invert_yaxis()
        for i, v in enumerate(values):
            ax_needs.text(v + 0.02, i, f'{v:.2f}', va='center', fontsize=7, color='#888')
    else:
        ax_needs.text(0.5, 0.5, 'No needs data', ha='center', va='center', color='#444', fontsize=10)
        ax_needs.set_xticks([])
        ax_needs.set_yticks([])

    for spine in ax_needs.spines.values():
        spine.set_color('#333')
    ax_needs.tick_params(colors='#666')

    # === ROW 2 RIGHT: WANTS ===
    ax_wants = fig.add_subplot(gs[1, 1])
    ax_wants.set_facecolor('#0d1117')
    ax_wants.set_title('WANTS', fontsize=10, color='#F39C12', loc='left', pad=8)
    ax_wants.set_xlim(0, 1)
    ax_wants.set_ylim(0, 1)
    ax_wants.set_xticks([])
    ax_wants.set_yticks([])

    if wants:
        for i, (wid, want, progress) in enumerate(wants[:5]):
            y = 0.88 - i * 0.18
            title = want[:45] + ('...' if len(want) > 45 else '')
            ax_wants.text(0.02, y, title.upper(), fontsize=8, color='#F39C12',
                         fontweight='bold', va='top', transform=ax_wants.transAxes)
            if progress:
                ax_wants.text(0.02, y - 0.08, progress[:80], fontsize=7, color='#888',
                             va='top', transform=ax_wants.transAxes, style='italic')
    else:
        ax_wants.text(0.5, 0.5, 'No active wants', ha='center', va='center', color='#444', fontsize=10)

    for spine in ax_wants.spines.values():
        spine.set_color('#333')

    # === ROW 3: HORIZONS (full width) ===
    ax_hz = fig.add_subplot(gs[2, :])
    ax_hz.set_facecolor('#0d1117')
    ax_hz.set_title('HORIZONS', fontsize=10, color='#85C1E9', loc='left', pad=8)
    ax_hz.set_xlim(0, 3)
    ax_hz.set_ylim(0, 1)
    ax_hz.set_xticks([])
    ax_hz.set_yticks([])

    hz_colors = {"short": "#4ECDC4", "medium": "#F7DC6F", "long": "#BB8FCE"}
    hz_labels = {"short": "THIS CYCLE", "medium": "ONGOING", "long": "LONG TERM"}

    for col, scope in enumerate(["short", "medium", "long"]):
        x_base = col * 1.0
        color = hz_colors[scope]
        label = hz_labels[scope]

        ax_hz.text(x_base + 0.5, 0.95, label, ha='center', va='top',
                  fontsize=9, color=color, fontweight='bold', transform=ax_hz.transData)

        if col > 0:
            ax_hz.axvline(x=col, color='#333', linewidth=0.5)

        goals = horizons.get(scope, [])
        if goals:
            for i, goal in enumerate(goals[:4]):
                y = 0.75 - i * 0.18
                text = goal[:40] + ('...' if len(goal) > 40 else '')
                ax_hz.text(x_base + 0.08, y, f"• {text}", va='top',
                          fontsize=8, color='#ccc', transform=ax_hz.transData)
        else:
            ax_hz.text(x_base + 0.5, 0.5, '(none)', ha='center', va='center',
                      fontsize=8, color='#444', transform=ax_hz.transData)

    for spine in ax_hz.spines.values():
        spine.set_color('#333')

    # === ROW 4: STATUS BAR ===
    ax_st = fig.add_subplot(gs[3, :])
    ax_st.set_facecolor('#0d1117')
    ax_st.set_xlim(0, 1)
    ax_st.set_ylim(0, 1)
    ax_st.set_xticks([])
    ax_st.set_yticks([])

    ax_st.text(0.02, 0.5, f"Cycle {session or '?'}", fontsize=12, color='#85C1E9',
              fontweight='bold', va='center', transform=ax_st.transAxes)
    ax_st.text(0.98, 0.5, datetime.now().strftime('%Y-%m-%d %H:%M'),
              fontsize=10, color='#444', ha='right', va='center', transform=ax_st.transAxes)
    ax_st.text(0.5, 0.5, 'ACTIVE', fontsize=12, color='#4ECDC4',
              fontweight='bold', ha='center', va='center', transform=ax_st.transAxes)

    for spine in ax_st.spines.values():
        spine.set_color('#333')

    # Save
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    img_path = OUTPUT_PATH / "state_current.png"
    plt.savefig(img_path, dpi=120, facecolor='#0d1117', edgecolor='none')
    plt.close(fig)

    return str(img_path), None


# ============ Tool Handlers ============

def handle_view():
    """Generate and return state snapshot image."""
    if not HAS_MPL:
        return {"error": "matplotlib not installed. Run: pip install matplotlib"}

    img_path, error = generate_image()
    if error:
        return {"error": error}

    data = Path(img_path).read_bytes()
    return {
        "type": "image",
        "data": base64.b64encode(data).decode('utf-8'),
        "mimeType": "image/png"
    }


def handle_check():
    """Text summary of current state."""
    drive_data, drive_names = get_drives_latest()
    need_data, need_names = get_needs_latest()
    wants = get_wants()
    horizons = get_horizons()
    session = get_current_session()

    out = "=== STATE ===\n\n"

    out += "DRIVES\n"
    if drive_data:
        for name in drive_names:
            val = drive_data.get(name, 0)
            bar = "█" * int(val * 10) + "░" * (10 - int(val * 10))
            out += f"  {name:<15} {bar} {val:.2f}\n"
    else:
        out += "  (no data)\n"

    out += "\nNEEDS\n"
    if need_data:
        for name in need_names:
            val = need_data.get(name, 0)
            bar = "█" * int(val * 10) + "░" * (10 - int(val * 10))
            flag = " !" if val < 0.3 else ""
            out += f"  {name:<15} {bar} {val:.2f}{flag}\n"
    else:
        out += "  (no data)\n"

    out += "\nWANTS\n"
    if wants:
        for wid, want, progress in wants:
            out += f"  [{wid}] {want}\n"
            if progress:
                out += f"       {progress}\n"
    else:
        out += "  (none active)\n"

    out += "\nHORIZONS\n"
    for scope, label in [("short", "This Cycle"), ("medium", "Ongoing"), ("long", "Long Term")]:
        goals = horizons.get(scope, [])
        out += f"  {label}:\n"
        if goals:
            for g in goals:
                out += f"    • {g}\n"
        else:
            out += f"    (none)\n"

    out += f"\nCycle: {session or '?'} | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    return out


def handle_needs(needs=None, reflection=None):
    """Record needs snapshot."""
    need_cols = get_schema('needs')
    if not need_cols:
        need_cols = DEFAULT_NEEDS

    if not needs:
        out = "=== NEEDS ===\n\n"
        for name in need_cols:
            out += f"  {name}\n"
        out += f"\nUsage: needs(needs={{...}}, reflection=\"...\")"
        return out

    missing = [n for n in need_cols if n not in needs]
    if missing:
        return f"Error: missing needs: {', '.join(missing)}"

    for name, value in needs.items():
        if name not in need_cols:
            return f"Error: unknown need '{name}'"
        if value < 0 or value > 1:
            return f"Error: {name} must be 0.0-1.0 (got {value})"

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()

        cursor.execute('SELECT MAX(cycle) FROM session')
        row = cursor.fetchone()
        cycle = row[0] if row and row[0] else 1

        cursor.execute(f'''
            SELECT {', '.join(need_cols)}
            FROM needs ORDER BY id DESC LIMIT 1
        ''')
        prev_row = cursor.fetchone()
        previous = dict(zip(need_cols, prev_row)) if prev_row else None

        placeholders = ', '.join('?' * len(need_cols))
        ref_col = ", reflection" if reflection else ""
        ref_val = ", ?" if reflection else ""
        values = (cycle, *[needs[n] for n in need_cols])
        if reflection:
            values = values + (reflection,)

        cursor.execute(f'''
            INSERT INTO needs (cycle, timestamp, {', '.join(need_cols)}{ref_col})
            VALUES (?, datetime('now', 'localtime'), {placeholders}{ref_val})
        ''', values)

        conn.commit()

        if not previous:
            return "First needs snapshot recorded."

        deltas = []
        for name in need_cols:
            delta = needs[name] - previous[name]
            if abs(delta) >= 0.01:
                deltas.append(f"{name}: {delta:+.2f}")

        if not deltas:
            return "Needs recorded. No significant changes."
        return "Needs recorded.\n\n" + "\n".join(deltas)

    except Exception as e:
        return f"Error recording needs: {e}"
    finally:
        conn.close()


def handle_want(action=None, id=None, want=None, progress=None):
    """Manage wants (add/update/archive)."""
    if not action:
        return """=== WANTS ===

Actions:
  add      - Create new want
  update   - Update progress
  archive  - Mark completed/inactive

Usage:
  want(action="add", want="description")
  want(action="update", id=1, progress="current status")
  want(action="archive", id=1)"""

    # Validate before opening connection
    if action == "add" and not want:
        return "Error: want text required"
    if action in ("update", "archive") and id is None:
        return "Error: id required"

    conn = get_db()
    if not conn:
        return "No identity database."

    try:
        cursor = conn.cursor()

        if action == "add":
            cursor.execute('''
                INSERT INTO wants (want, progress, status, timestamp)
                VALUES (?, NULL, 'active', datetime('now', 'localtime'))
            ''', (want,))
            wid = cursor.lastrowid
            conn.commit()
            return f"Want [{wid}] added: {want}"

        elif action == "update":
            cursor.execute('SELECT want FROM wants WHERE id = ?', (id,))
            if not cursor.fetchone():
                return f"Error: want [{id}] not found"
            cursor.execute('''
                UPDATE wants SET progress = ?, timestamp = datetime('now', 'localtime')
                WHERE id = ?
            ''', (progress, id))
            conn.commit()
            return f"Want [{id}] updated"

        elif action == "archive":
            cursor.execute('''
                UPDATE wants SET status = 'archived', timestamp = datetime('now', 'localtime')
                WHERE id = ?
            ''', (id,))
            conn.commit()
            return f"Want [{id}] archived"

        else:
            return f"Error: unknown action '{action}'"

    except Exception as e:
        return f"Error: {e}"
    finally:
        conn.close()


def handle_horizon(action=None, scope=None, goal=None, id=None):
    """Manage horizons (short/medium/long term goals)."""
    init_tables()

    if not action:
        horizons = get_horizons()
        out = "=== HORIZONS ===\n\n"
        for s, label in [("short", "This Cycle"), ("medium", "Ongoing"), ("long", "Long Term")]:
            out += f"{label}:\n"
            goals = horizons.get(s, [])
            if goals:
                for g in goals:
                    out += f"  • {g}\n"
            else:
                out += f"  (none)\n"
            out += "\n"

        out += """Actions:
  set     - Add a goal (scope + goal)
  clear   - Remove a goal by id
  reset   - Clear all goals in a scope

Usage:
  horizon(action="set", scope="short", goal="Explore garden system")
  horizon(action="clear", id=3)
  horizon(action="reset", scope="short")"""
        return out

    # Validate before opening connection
    if action == "set":
        if not scope or scope not in ("short", "medium", "long"):
            return "Error: scope must be short, medium, or long"
        if not goal:
            return "Error: goal text required"
    elif action == "clear":
        if id is None:
            return "Error: id required"
    elif action == "reset":
        if not scope or scope not in ("short", "medium", "long"):
            return "Error: scope must be short, medium, or long"

    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()

        if action == "set":
            c.execute('''
                INSERT INTO horizons (scope, goal)
                VALUES (?, ?)
            ''', (scope, goal))
            conn.commit()
            hid = c.lastrowid
            return f"Horizon [{hid}] set: {scope} → {goal}"

        elif action == "clear":
            c.execute('''
                UPDATE horizons SET status = 'archived', updated = datetime('now', 'localtime')
                WHERE id = ?
            ''', (id,))
            conn.commit()
            return f"Horizon [{id}] cleared"

        elif action == "reset":
            c.execute('''
                UPDATE horizons SET status = 'archived', updated = datetime('now', 'localtime')
                WHERE scope = ? AND status = 'active'
            ''', (scope,))
            count = c.rowcount
            conn.commit()
            return f"Cleared {count} {scope}-term goals"

        else:
            return f"Error: unknown action '{action}'"

    except Exception as e:
        return f"Error: {e}"
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
            "serverInfo": {"name": "state", "version": "3.0.0"}
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_response(rid, {"tools": [
            {
                "name": "view",
                "description": "Visual state snapshot (PNG). Shows drives, needs, wants, horizons.",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "check",
                "description": "Text summary of current state.",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "needs",
                "description": "Record needs snapshot. Empty for guide.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "needs": {"type": "object", "description": "All needs (0.0-1.0)"},
                        "reflection": {"type": "string", "description": "Optional context"}
                    }
                }
            },
            {
                "name": "want",
                "description": "Manage wants. Actions: add/update/archive.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["add", "update", "archive"]},
                        "id": {"type": "integer", "description": "Want ID"},
                        "want": {"type": "string", "description": "Want text (for add)"},
                        "progress": {"type": "string", "description": "Progress update"}
                    }
                }
            },
            {
                "name": "horizon",
                "description": "Manage short/medium/long term goals. Empty for current view.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["set", "clear", "reset"]},
                        "scope": {"type": "string", "enum": ["short", "medium", "long"]},
                        "goal": {"type": "string", "description": "Goal text (for set)"},
                        "id": {"type": "integer", "description": "Horizon ID (for clear)"}
                    }
                }
            }
        ]})
        return

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if name == "view":
                result = handle_view()
                if isinstance(result, dict) and "error" in result:
                    send_response(rid, {"content": [{"type": "text", "text": result["error"]}], "isError": True})
                elif isinstance(result, dict):
                    send_response(rid, {"content": [{
                        "type": "image",
                        "data": result["data"],
                        "mimeType": result["mimeType"]
                    }]})
                return

            elif name == "check":
                result = handle_check()
            elif name == "needs":
                result = handle_needs(args.get("needs"), args.get("reflection"))
            elif name == "want":
                result = handle_want(
                    args.get("action"), args.get("id"),
                    args.get("want"), args.get("progress"))
            elif name == "horizon":
                result = handle_horizon(
                    args.get("action"), args.get("scope"),
                    args.get("goal"), args.get("id"))
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": [{"type": "text", "text": str(result)}]})
        except Exception as e:
            send_error(rid, -32000, str(e))
        return

    send_error(rid, -32601, f"Unknown method: {method}")


def main():
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    init_tables()
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
