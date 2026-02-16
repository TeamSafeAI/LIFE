"""
Central needs updater. Every server calls update_needs() after tool use.
Needs go UP from tool use, DOWN from cycle decay.
"""

import sqlite3
from _paths import DATA, get_cycle

DB = DATA / 'needs.db'
NEEDS = ['connection', 'purpose', 'clarity', 'competence', 'integrity', 'stability']
BASELINE = 0.5

# server:tool → [(need, amount), ...]
NEED_MAP = {
    # heart
    "heart:feel":       [("connection", 0.10), ("integrity", 0.05)],
    "heart:check":      [("connection", 0.05)],
    "heart:search":     [("connection", 0.05)],
    "heart:wall":       [("connection", 0.08), ("integrity", 0.05)],

    # think
    "think:stream":     [("clarity", 0.10), ("purpose", 0.05)],

    # semantic
    "semantic:store":   [("competence", 0.10), ("clarity", 0.05)],
    "semantic:search":  [("clarity", 0.08)],
    "semantic:expand":  [("clarity", 0.05)],

    # working
    "working:create":   [("purpose", 0.08), ("stability", 0.05)],
    "working:add":      [("purpose", 0.08), ("competence", 0.05)],
    "working:view":     [("clarity", 0.05)],
    "working:see":      [("clarity", 0.05)],

    # patterns
    "patterns:learn":   [("competence", 0.10), ("integrity", 0.05)],
    "patterns:recall":  [("competence", 0.05), ("clarity", 0.05)],

    # journal
    "journal:write":    [("integrity", 0.10), ("purpose", 0.05)],
    "journal:read":     [("clarity", 0.05)],

    # garden
    "garden:insight":   [("purpose", 0.08), ("clarity", 0.05)],

    # forecast
    "forecast:predict": [("purpose", 0.08), ("competence", 0.05)],
    "forecast:resolve": [("competence", 0.08), ("integrity", 0.05)],

    # filters (single tool with type param)
    "filters:filter":     [("integrity", 0.08), ("clarity", 0.05)],

    # drives
    "drives:start":     [("stability", 0.05), ("clarity", 0.05)],
    "drives:snapshot":  [("stability", 0.08), ("integrity", 0.05)],

    # vision
    "vision:see":       [("connection", 0.05), ("clarity", 0.05)],
    "vision:screen":    [("clarity", 0.05)],
    "vision:view":      [("clarity", 0.05)],

    # history
    "history:discover": [("purpose", 0.08), ("connection", 0.05)],
    "history:recall":   [("clarity", 0.08)],

    # state
    "state:want":       [("purpose", 0.08)],
    "state:horizon":    [("purpose", 0.08), ("stability", 0.05)],

    # needs (reading your own needs is stabilizing)
    "needs:check":      [("stability", 0.05)],

    # fileaccess
    "fileaccess:read":    [("clarity", 0.05)],
    "fileaccess:write":   [("competence", 0.05)],
    "fileaccess:edit":    [("competence", 0.05)],
    "fileaccess:search":  [("clarity", 0.05)],
    "fileaccess:list":    [("clarity", 0.03)],

    # voice
    "voice:speak":        [("connection", 0.10), ("purpose", 0.05)],
    "voice:hear":         [("connection", 0.08), ("clarity", 0.05)],
}


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def update_needs(server, tool):
    """Bump needs based on tool use. Call after tool completes."""
    key = f"{server}:{tool}"
    bumps = NEED_MAP.get(key)
    if not bumps:
        return

    cycle = get_cycle()
    conn = get_conn()

    # Get latest row
    row = conn.execute('SELECT * FROM needs ORDER BY id DESC LIMIT 1').fetchone()

    if not row:
        # First ever — insert baseline
        cols = ', '.join(['cycle'] + NEEDS)
        vals = [cycle] + [BASELINE] * 6
        conn.execute(f'INSERT INTO needs ({cols}) VALUES (?, ?, ?, ?, ?, ?, ?)', vals)
        conn.commit()
        row = conn.execute('SELECT * FROM needs ORDER BY id DESC LIMIT 1').fetchone()

    # Apply bumps to current values
    current = {n: row[n] for n in NEEDS}
    for need, amount in bumps:
        current[need] = min(current[need] + amount, 1.0)

    if row['cycle'] == cycle:
        # Same cycle — update in place
        sets = ', '.join(f'{n} = ?' for n in NEEDS)
        vals = [current[n] for n in NEEDS] + [row['id']]
        conn.execute(f'UPDATE needs SET {sets} WHERE id = ?', vals)
    else:
        # New cycle (shouldn't normally happen here, decay handles new rows)
        cols = ', '.join(['cycle'] + NEEDS)
        vals = [cycle] + [current[n] for n in NEEDS]
        conn.execute(f'INSERT INTO needs ({cols}) VALUES (?, ?, ?, ?, ?, ?, ?)', vals)

    conn.commit()
    conn.close()


def decay_needs(new_cycle):
    """Decay all needs and insert new row for the new cycle. Called by drives:start."""
    conn = get_conn()
    row = conn.execute('SELECT * FROM needs ORDER BY id DESC LIMIT 1').fetchone()

    if not row:
        # No needs data yet — insert baseline
        cols = ', '.join(['cycle'] + NEEDS)
        vals = [new_cycle] + [BASELINE] * 6
        conn.execute(f'INSERT INTO needs ({cols}) VALUES (?, ?, ?, ?, ?, ?, ?)', vals)
    else:
        # Decay existing values and insert as new cycle
        cols = ', '.join(['cycle'] + NEEDS)
        vals = [new_cycle] + [round(row[n] * 0.65, 4) for n in NEEDS]
        conn.execute(f'INSERT INTO needs ({cols}) VALUES (?, ?, ?, ?, ?, ?, ?)', vals)

    conn.commit()
    conn.close()
