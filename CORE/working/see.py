"""
See handler — visual render of working memory threads.
No params: board overview. With thread: single thread detail.
"""

import base64
import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA, VISUAL, get_cycle
from db import get_conn, temperature

DB = DATA / 'working.db'
OUTPUT = VISUAL
OUTPUT.mkdir(parents=True, exist_ok=True)

# --- Config (matches HEARTH palette) ---
BG = '#0d1117'
PANEL_BG = '#161b22'
TEXT = '#c9d1d9'
ACCENT = '#58a6ff'
GRID = '#21262d'
MUTED = '#6e7681'

TEMP_COLORS = {
    'HOT': '#f97583',
    'WARM': '#ffa657',
    'COLD': '#6e7681',
}


def _query(sql, params=()):
    if not DB.exists():
        return []
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def _image_response(fig):
    """Save figure to VISUAL, return base64 image response."""
    path = OUTPUT / 'working.png'
    fig.savefig(path, dpi=120, facecolor=BG)
    plt.close(fig)
    img_bytes = path.read_bytes()
    return [{
        "type": "image",
        "data": base64.b64encode(img_bytes).decode('utf-8'),
        "mimeType": "image/png"
    }]


def _render_board():
    """Overview board — all threads, temp-coded, with note counts."""
    current = get_cycle()

    rows = _query('''
        SELECT t.id, t.title, t.content, t.created_cycle, t.last_touched_cycle,
               (SELECT COUNT(*) FROM notes WHERE thread_id = t.id) AS note_count
        FROM topics t
        ORDER BY t.last_touched_cycle DESC
        LIMIT 30
    ''')

    if not rows:
        return [{"type": "text", "text": "No threads."}]

    # Group by temperature
    hot, warm, cold = [], [], []
    for r in rows:
        temp = temperature(r['last_touched_cycle'], current)
        if temp == 'HOT':
            hot.append(r)
        elif temp == 'WARM':
            warm.append(r)
        else:
            cold.append(r)

    groups = []
    if hot:
        groups.append(('HOT', hot))
    if warm:
        groups.append(('WARM', warm))
    if cold:
        groups.append(('COLD', cold))

    fig = plt.figure(figsize=(12, max(4, len(rows) * 0.45 + 1.5)), facecolor=BG)
    ax = fig.add_subplot(111)
    ax.set_facecolor(PANEL_BG)
    ax.set_xlim(0, 1)
    ax.axis('off')

    fig.text(0.04, 0.97, f'WORKING MEMORY', color=ACCENT, fontsize=16,
             fontweight='bold', va='top')
    fig.text(0.04, 0.935, f'cycle {current}  |  {len(rows)} threads',
             color=MUTED, fontsize=10, va='top')

    y = 0.88

    for label, threads in groups:
        color = TEMP_COLORS[label]

        # Group header
        ax.text(0.02, y, f'— {label} —', color=color, fontsize=12,
                fontweight='bold', transform=ax.transAxes)
        y -= 0.06

        for r in threads:
            title = r['title']
            if len(title) > 50:
                title = title[:47] + '...'

            content = r['content'] or ''
            if len(content) > 60:
                content = content[:57] + '...'

            # Thread title + note count
            ax.text(0.04, y, f'● {title}', color=TEXT, fontsize=10,
                    fontweight='bold', transform=ax.transAxes)
            ax.text(0.85, y, f'{r["note_count"]} notes', color=MUTED, fontsize=8,
                    ha='right', transform=ax.transAxes)
            y -= 0.04

            # Content summary
            if content:
                ax.text(0.06, y, content, color=MUTED, fontsize=8,
                        transform=ax.transAxes)
            y -= 0.05

        y -= 0.02  # gap between groups

    # Set y limits based on content
    total_height = 0.88 - y
    ax.set_ylim(0, 1)

    for spine in ax.spines.values():
        spine.set_color(GRID)

    return _image_response(fig)


def _render_thread(thread_name):
    """Single thread detail — title, content, notes listed."""
    current = get_cycle()

    topic = _query('SELECT * FROM topics WHERE title = ?', (thread_name,))
    if not topic:
        return [{"type": "text", "text": f"Thread '{thread_name}' not found."}]

    topic = topic[0]
    notes = _query(
        'SELECT title, content FROM notes WHERE thread_id = ? ORDER BY id ASC',
        (topic['id'],)
    )

    temp = temperature(topic['last_touched_cycle'], current)
    temp_color = TEMP_COLORS[temp]

    fig_height = max(4, 2 + len(notes) * 0.6)
    fig = plt.figure(figsize=(12, fig_height), facecolor=BG)
    ax = fig.add_subplot(111)
    ax.set_facecolor(PANEL_BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # Header
    fig.text(0.04, 0.97, topic['title'], color=ACCENT, fontsize=16,
             fontweight='bold', va='top')
    fig.text(0.04, 0.935,
             f'{temp}  |  created cycle {topic["created_cycle"]}  |  '
             f'touched cycle {topic["last_touched_cycle"]}  |  {len(notes)} notes',
             color=temp_color, fontsize=10, va='top')

    y = 0.88

    # Content
    content = topic['content'] or ''
    if content:
        # Wrap long content
        lines = []
        while content:
            if len(content) <= 90:
                lines.append(content)
                break
            cut = content[:90].rfind(' ')
            if cut <= 0:
                cut = 90
            lines.append(content[:cut])
            content = content[cut:].lstrip()

        for line in lines:
            ax.text(0.03, y, line, color=TEXT, fontsize=10,
                    transform=ax.transAxes)
            y -= 0.045

    y -= 0.03

    # Notes
    if notes:
        ax.text(0.02, y, 'NOTES', color=ACCENT, fontsize=11,
                fontweight='bold', transform=ax.transAxes)
        y -= 0.06

        for n in notes:
            note_title = n['title'] or ''
            note_content = n['content'] or ''

            if len(note_title) > 50:
                note_title = note_title[:47] + '...'

            ax.text(0.04, y, f'● {note_title}', color=TEXT, fontsize=9,
                    fontweight='bold', transform=ax.transAxes)
            y -= 0.04

            if note_content:
                if len(note_content) > 80:
                    note_content = note_content[:77] + '...'
                ax.text(0.06, y, note_content, color=MUTED, fontsize=8,
                        transform=ax.transAxes)
                y -= 0.04

            y -= 0.02
    else:
        ax.text(0.03, y, 'no notes yet', color=MUTED, fontsize=10,
                transform=ax.transAxes)

    for spine in ax.spines.values():
        spine.set_color(GRID)

    return _image_response(fig)


def handle_see(args):
    thread = args.get('thread', '').strip() if args.get('thread') else ''

    if not thread:
        return _render_board()
    return _render_thread(thread)
