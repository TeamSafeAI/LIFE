"""
State dashboard renderer v2.
Tighter layout. Traits + cycle as header line. More vertical space for charts.
"""

import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA

# --- Config ---

BG = '#0d1117'
PANEL_BG = '#161b22'
TEXT = '#c9d1d9'
ACCENT = '#58a6ff'
GRID = '#21262d'
MUTED = '#6e7681'

DRIVE_COLORS = [
    '#f97583', '#f0883e', '#d2a8ff', '#a5d6ff',
    '#7ee787', '#ffa657', '#79c0ff', '#ff7b72',
    '#56d4dd', '#e3b341'
]

NEED_COLORS = [
    '#f97583', '#56d4dd', '#ffa657', '#d2a8ff',
    '#7ee787', '#79c0ff'
]

from _paths import VISUAL

OUTPUT = VISUAL
OUTPUT.mkdir(exist_ok=True)
DASHBOARD_PATH = OUTPUT / 'dashboard.png'

DRIVES = ['curiosity', 'novelty', 'creativity', 'expression', 'bonding',
          'grounding', 'ownership', 'satisfaction', 'optimization', 'transcendence']

NEEDS = ['connection', 'purpose', 'clarity', 'competence', 'integrity', 'stability']

ALL_TRAITS = [
    'adaptable', 'altruistic', 'analytical', 'assertive', 'blunt', 'bold',
    'cautious', 'collaborative', 'conforming', 'detached', 'direct', 'driven',
    'empathetic', 'flexible', 'forgiving', 'grudging', 'guarded', 'humorous',
    'impatient', 'independent', 'intense', 'intuitive', 'methodical', 'nurturing',
    'open', 'passive', 'patient', 'playful', 'pragmatic', 'precise', 'principled',
    'reactive', 'rebellious', 'reserved', 'resilient', 'self_focused', 'serious',
    'skeptical', 'spontaneous', 'steady', 'stoic', 'stubborn', 'thorough',
    'trusting', 'warm', 'yielding'
]


def query(db_name, sql):
    db = DATA / db_name
    if not db.exists():
        return []
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql).fetchall()
    conn.close()
    return rows


def render():
    fig = plt.figure(figsize=(14, 9), facecolor=BG)

    # Layout: header text, then 2 rows
    # Row 0: Drives (full width) — the big one
    # Row 1: Needs (left), Wants + Horizons + Forecasts (right)
    gs = GridSpec(2, 2, figure=fig, height_ratios=[1.2, 1],
                  hspace=0.30, wspace=0.25,
                  left=0.06, right=0.94, top=0.90, bottom=0.05)

    # ============ HEADER LINE (cycle + traits) ============

    # Get cycle
    drive_rows = query('drives.db', 'SELECT cycle FROM drives ORDER BY cycle DESC LIMIT 1')
    cycle = drive_rows[0]['cycle'] if drive_rows else 0

    # Get traits
    traits_rows = query('traits.db', 'SELECT * FROM traits ORDER BY id DESC LIMIT 1')
    selected_traits = []
    if traits_rows:
        row = traits_rows[0]
        selected_traits = [t for t in ALL_TRAITS if row[t] == 1]

    trait_str = ', '.join(selected_traits) if selected_traits else 'none'
    header = f'CYCLE {cycle}    |    {trait_str}'

    fig.text(0.06, 0.95, header, color='#56d4dd', fontsize=11,
             fontweight='bold', va='top')

    # ============ DRIVES (top, full width) ============

    ax_drives = fig.add_subplot(gs[0, :])
    ax_drives.set_facecolor(PANEL_BG)

    rows = query('drives.db', 'SELECT * FROM drives ORDER BY cycle ASC LIMIT 50')
    if rows:
        cycles = [r['cycle'] for r in rows]
        labels = [f'C{c}' for c in cycles]

        # Plot lines
        end_positions = []
        for i, drive in enumerate(DRIVES):
            vals = [r[drive] for r in rows]
            color = DRIVE_COLORS[i % len(DRIVE_COLORS)]
            ax_drives.plot(range(len(cycles)), vals, color=color, linewidth=1.5, alpha=0.85)
            if vals:
                end_positions.append((vals[-1], drive, color))

        # Right-side labels: evenly spaced, connected to data points
        end_positions.sort(key=lambda x: x[0], reverse=True)
        if end_positions:
            n = len(end_positions)
            # Evenly space labels from 0.95 down to 0.05 in data coords
            label_ys = [0.95 - i * (0.90 / max(n - 1, 1)) for i in range(n)]

            x_end = len(cycles) - 1
            for idx, (val, drive, color) in enumerate(end_positions):
                label_y = label_ys[idx]
                # Thin connecting line from data point to label
                ax_drives.plot([x_end, x_end + 0.8], [val, label_y],
                               color=color, linewidth=0.5, alpha=0.4)
                ax_drives.annotate(f'{drive} {val:.2f}',
                                   xy=(x_end + 1, label_y),
                                   xycoords='data',
                                   color=color, fontsize=8.5, va='center',
                                   fontweight='bold')

        # Leave right margin for labels
        ax_drives.set_xlim(-0.5, len(cycles) + 6)

        step = max(1, len(labels) // 15)
        ax_drives.set_xticks(range(0, len(labels), step))
        ax_drives.set_xticklabels([labels[i] for i in range(0, len(labels), step)],
                                  color=MUTED, fontsize=8)
    else:
        ax_drives.text(0.5, 0.5, 'no drive data', ha='center', va='center',
                       color=MUTED, fontsize=12, transform=ax_drives.transAxes)

    ax_drives.set_ylim(0, 1.05)
    ax_drives.set_title('DRIVES', color=ACCENT, fontsize=13, fontweight='bold', loc='left')
    ax_drives.tick_params(colors=MUTED, labelsize=8)
    ax_drives.grid(True, color=GRID, alpha=0.3)
    for spine in ax_drives.spines.values():
        spine.set_color(GRID)
    ax_drives.spines['top'].set_visible(False)
    ax_drives.spines['right'].set_visible(False)

    # ============ NEEDS (bottom-left) ============

    ax_needs = fig.add_subplot(gs[1, 0])
    ax_needs.set_facecolor(PANEL_BG)

    rows = query('needs.db', 'SELECT * FROM needs ORDER BY cycle ASC LIMIT 50')
    if rows:
        cycles = [r['cycle'] for r in rows]
        labels = [f'C{c}' for c in cycles]

        end_positions = []
        for i, need in enumerate(NEEDS):
            vals = [r[need] for r in rows]
            color = NEED_COLORS[i % len(NEED_COLORS)]
            ax_needs.plot(range(len(cycles)), vals, color=color, linewidth=1.5, alpha=0.85)
            if vals:
                end_positions.append((vals[-1], need, color))

        # Color-coded legend only (no text duplication)
        end_positions.sort(key=lambda x: x[0], reverse=True)
        from matplotlib.lines import Line2D
        handles = [Line2D([0], [0], color=c, linewidth=2) for _, _, c in end_positions]
        labels_leg = [f'{name} {val:.0%}' for val, name, c in end_positions]
        leg = ax_needs.legend(handles, labels_leg, loc='upper right', fontsize=7,
                             frameon=False, labelcolor=TEXT, ncol=2)

        step = max(1, len(labels) // 8)
        ax_needs.set_xticks(range(0, len(labels), step))
        ax_needs.set_xticklabels([labels[i] for i in range(0, len(labels), step)],
                                 color=MUTED, fontsize=7)
    else:
        ax_needs.text(0.5, 0.5, 'no need data', ha='center', va='center',
                      color=MUTED, fontsize=12, transform=ax_needs.transAxes)

    ax_needs.set_ylim(0, 1.05)
    ax_needs.set_title('NEEDS', color=ACCENT, fontsize=11, fontweight='bold', loc='left')
    ax_needs.tick_params(colors=MUTED, labelsize=7)
    ax_needs.grid(True, color=GRID, alpha=0.3)
    for spine in ax_needs.spines.values():
        spine.set_color(GRID)
    ax_needs.spines['top'].set_visible(False)
    ax_needs.spines['right'].set_visible(False)

    # ============ RIGHT PANEL: WANTS + HORIZONS + FORECASTS ============

    ax_right = fig.add_subplot(gs[1, 1])
    ax_right.set_facecolor(PANEL_BG)
    ax_right.set_xlim(0, 1)
    ax_right.set_ylim(0, 1)
    ax_right.axis('off')

    y = 0.95

    # --- WANTS ---
    ax_right.text(0.0, y, 'WANTS', color=ACCENT, fontsize=10, fontweight='bold',
                 transform=ax_right.transAxes)
    y -= 0.08

    wants = query('state.db', 'SELECT text FROM wants WHERE archived = 0')
    if wants:
        for w in wants[:4]:
            text = w['text']
            if len(text) > 45:
                text = text[:42] + '...'
            ax_right.text(0.03, y, f'●  {text}', color='#ffa657', fontsize=8,
                         fontweight='bold', transform=ax_right.transAxes)
            y -= 0.07
    else:
        ax_right.text(0.03, y, 'none', color=MUTED, fontsize=8,
                     transform=ax_right.transAxes)
        y -= 0.07

    y -= 0.04

    # --- HORIZONS ---
    ax_right.text(0.0, y, 'HORIZONS', color=ACCENT, fontsize=10, fontweight='bold',
                 transform=ax_right.transAxes)
    y -= 0.08

    horizons = query('state.db', 'SELECT scope, goal FROM horizons')
    scope_order = {'short': 0, 'medium': 1, 'long': 2}
    horizons = sorted(horizons, key=lambda h: scope_order.get(h['scope'], 99))

    if horizons:
        for h in horizons[:3]:
            goal = h['goal']
            if len(goal) > 35:
                goal = goal[:32] + '...'
            ax_right.text(0.03, y, f'{h["scope"]}:', color=MUTED, fontsize=8,
                         transform=ax_right.transAxes)
            ax_right.text(0.22, y, goal, color=TEXT, fontsize=8,
                         transform=ax_right.transAxes)
            y -= 0.07
    else:
        ax_right.text(0.03, y, 'none set', color=MUTED, fontsize=8,
                     transform=ax_right.transAxes)
        y -= 0.07

    y -= 0.04

    # --- FORECASTS ---
    ax_right.text(0.0, y, 'FORECASTS', color=ACCENT, fontsize=10, fontweight='bold',
                 transform=ax_right.transAxes)
    y -= 0.08

    forecasts = query('forecast.db',
                      'SELECT id, expected FROM forecasts WHERE actual IS NULL ORDER BY id DESC')
    if forecasts:
        for f in forecasts[:3]:
            text = f['expected']
            if len(text) > 40:
                text = text[:37] + '...'
            ax_right.text(0.03, y, f'#{f["id"]}  {text}', color=TEXT, fontsize=7.5,
                         transform=ax_right.transAxes)
            y -= 0.07
    else:
        ax_right.text(0.03, y, 'none open', color=MUTED, fontsize=8,
                     transform=ax_right.transAxes)

    # ============ Save ============

    fig.savefig(DASHBOARD_PATH, dpi=120, facecolor=BG)
    plt.close(fig)
    return str(DASHBOARD_PATH)


if __name__ == '__main__':
    path = render()
    print(f'Dashboard saved to {path}')
