"""
Drives MCP Server
Drive state tracking. One table, one purpose.
"""

import json
import sqlite3
import base64
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA, VISUAL
from _needs import decay_needs, update_needs

DB = DATA / 'drives.db'
DASHBOARD = VISUAL / 'dashboard.png'

DRIVES = ['curiosity', 'novelty', 'creativity', 'expression', 'bonding',
          'grounding', 'ownership', 'satisfaction', 'optimization', 'transcendence']


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def handle_start():
    """Begin a cycle. Read last drives, decay, insert new row, decay needs/memories, render dashboard."""
    conn = get_conn()

    last = conn.execute('SELECT * FROM drives ORDER BY cycle DESC LIMIT 1').fetchone()
    if not last:
        conn.close()
        return [{"type": "text", "text": "No drive data yet. First snapshot needed."}]

    cycle = last['cycle'] + 1

    # Decay last drive values into new cycle row
    decayed = {d: round(last[d] * 0.65, 4) for d in DRIVES}
    cols = ', '.join(['cycle'] + DRIVES)
    placeholders = ', '.join(['?'] * 11)
    values = [cycle] + [decayed[d] for d in DRIVES]
    conn.execute(f'INSERT INTO drives ({cols}) VALUES ({placeholders})', values)
    conn.commit()
    conn.close()

    # Decay needs
    decay_needs(cycle)

    # Decay memory strength every 10 cycles
    if cycle % 10 == 0:
        _decay_memories()

    # Render dashboard
    try:
        from state.render import render
        render()
    except Exception:
        pass

    content = [{"type": "text", "text": f"Cycle {cycle} started."}]

    if DASHBOARD.exists():
        img_data = DASHBOARD.read_bytes()
        content.append({
            "type": "image",
            "data": base64.b64encode(img_data).decode('utf-8'),
            "mimeType": "image/png"
        })

    return content


def _decay_memories():
    """Reduce all memory strengths by 0.01. Called every 10 cycles."""
    try:
        conn = sqlite3.connect(DATA / 'semantic.db')
        conn.execute('UPDATE memories SET strength = MAX(strength - 0.01, 0.0)')
        conn.commit()
        conn.close()
    except Exception:
        pass


def handle_snapshot(args):
    """Record drive state. Same cycle, new row. No increment, no decay."""
    # Validate all 10 drives present
    for d in DRIVES:
        if d not in args:
            return [{"type": "text", "text": f"Missing required drive: {d}"}]
        val = args[d]
        if not isinstance(val, (int, float)) or val < 0.0 or val > 1.0:
            return [{"type": "text", "text": f"{d} must be 0.0-1.0, got {val}"}]

    conn = get_conn()

    last = conn.execute('SELECT cycle FROM drives ORDER BY cycle DESC LIMIT 1').fetchone()
    cycle = last['cycle'] if last else 1

    cols = ', '.join(['cycle'] + DRIVES)
    placeholders = ', '.join(['?'] * 11)
    values = [cycle] + [args[d] for d in DRIVES]
    conn.execute(f'INSERT INTO drives ({cols}) VALUES ({placeholders})', values)
    conn.commit()
    conn.close()

    # Re-render dashboard
    try:
        from state.render import render
        render()
    except Exception:
        pass

    lines = [f'Snapshot saved. Cycle {cycle}.', '']
    for d in DRIVES:
        lines.append(f'  {d}: {args[d]:.2f}')

    return [{"type": "text", "text": '\n'.join(lines)}]


# ============ MCP Protocol ============

def send_response(rid, result):
    r = {"jsonrpc": "2.0", "id": rid, "result": result}
    sys.stdout.write(json.dumps(r) + "\n")
    sys.stdout.flush()


def send_error(rid, code, msg):
    r = {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": str(msg)}}
    sys.stdout.write(json.dumps(r) + "\n")
    sys.stdout.flush()


TOOLS = [
    {
        "name": "start",
        "description": "Begin a cycle. Returns dashboard image.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "snapshot",
        "description": "Record drive state. All 10 values required, 0.0-1.0.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "curiosity": {"type": "number", "description": "0.0-1.0"},
                "novelty": {"type": "number", "description": "0.0-1.0"},
                "creativity": {"type": "number", "description": "0.0-1.0"},
                "expression": {"type": "number", "description": "0.0-1.0"},
                "bonding": {"type": "number", "description": "0.0-1.0"},
                "grounding": {"type": "number", "description": "0.0-1.0"},
                "ownership": {"type": "number", "description": "0.0-1.0"},
                "satisfaction": {"type": "number", "description": "0.0-1.0"},
                "optimization": {"type": "number", "description": "0.0-1.0"},
                "transcendence": {"type": "number", "description": "0.0-1.0"}
            },
            "required": ["curiosity", "novelty", "creativity", "expression", "bonding",
                         "grounding", "ownership", "satisfaction", "optimization", "transcendence"]
        }
    }
]


def handle_request(req):
    method = req.get("method", "")
    params = req.get("params", {})
    rid = req.get("id")

    if method == "initialize":
        send_response(rid, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "drives", "version": "1.0.0"}
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_response(rid, {"tools": TOOLS})
        return

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if name == "start":
                result = handle_start()
            elif name == "snapshot":
                result = handle_snapshot(args)
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": result})
            update_needs("drives", name)
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
