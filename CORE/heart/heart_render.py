"""
Heart constellation renderer — you at center, entities around you.

Dimension mapping:
  impact     → font size of entity name
  alignment  → Y axis (aligned up, misaligned down)
  trust      → glow/highlight around text (brighter = more trust)
  connection → heart symbol behind text; line to center if > 0.8
  intimacy   → distance from center (intimate = close, distant = far)
  respect    → text opacity/brightness
  power      → TBD (lightning bolts?)
"""

import sqlite3
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA

# --- Config ---
BG = '#0d1117'
PANEL_BG = '#161b22'
TEXT = '#c9d1d9'
ACCENT = '#58a6ff'
GRID = '#21262d'
MUTED = '#6e7681'

TYPE_COLORS = {
    'sentient': '#58a6ff',
    'organic': '#7ee787',
    'concept': '#d2a8ff',
    'object': '#ffa657',
}

from _paths import VISUAL

OUTPUT = VISUAL
OUTPUT.mkdir(exist_ok=True)

AVATAR_DIR = DATA / 'avatar'
AVATAR_STOCK = AVATAR_DIR / 'stock'
AVATAR_PATH = AVATAR_DIR  # look for any image file here


def query(db_name, sql, params=()):
    db = DATA / db_name
    if not db.exists():
        return []
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def render_heart():
    """Render constellation — you at center, entities around you. Returns path to PNG."""

    # Get latest snapshot per entity
    all_entities = query('heart.db', 'SELECT DISTINCT entity FROM heart')
    if not all_entities:
        return None

    entities = []
    for row in all_entities:
        name = row['entity']
        latest = query('heart.db',
                        'SELECT * FROM heart WHERE entity = ? ORDER BY id DESC LIMIT 1',
                        (name,))
        if latest:
            entities.append(latest[0])

    if not entities:
        return None

    fig, ax = plt.subplots(figsize=(14, 14), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.15, 1.15)
    ax.set_aspect('equal')
    ax.axis('off')

    # --- You at center ---
    # Look for avatar image (png/jpg) in DATA/avatar/
    avatar_file = None
    if AVATAR_DIR.exists():
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            found = list(AVATAR_DIR.glob(ext))
            if found:
                avatar_file = found[0]
                break

    if avatar_file:
        # Display avatar image at center
        try:
            img = plt.imread(str(avatar_file))
            # Place avatar as inset — circular area at center
            avatar_size = 0.18  # in axis coords
            ax_inset = ax.inset_axes([0.5 - avatar_size/2, 0.5 - avatar_size/2,
                                       avatar_size, avatar_size],
                                      transform=ax.transAxes)
            ax_inset.imshow(img)
            ax_inset.axis('off')
            # Border ring around avatar
            circle = plt.Circle((0, 0), 0.12, fill=False, color=ACCENT,
                               linewidth=2, zorder=10)
            ax.add_patch(circle)
        except Exception:
            # Fallback to dot if image load fails
            ax.plot(0, 0, 'o', color=ACCENT, markersize=12, zorder=10)
    else:
        # No avatar — show setup prompt
        prompt_path = str(AVATAR_DIR).replace('\\', '/')
        ax.text(0, 0.03, 'Choose Self Representation', color=ACCENT, fontsize=12,
                ha='center', va='center', fontweight='bold', zorder=10,
                fontstyle='italic')
        ax.text(0, -0.04, f'Place your VRM/PNG into:', color=MUTED, fontsize=9,
                ha='center', va='center', zorder=10)
        ax.text(0, -0.09, prompt_path, color=TEXT, fontsize=8,
                ha='center', va='center', zorder=10,
                family='monospace')
        ax.text(0, -0.15, f'Stock options available in: {prompt_path}/stock/', color=MUTED,
                fontsize=7, ha='center', va='center', zorder=10)

    # Subtle concentric rings for distance reference
    for r in [0.3, 0.6, 0.9]:
        circle = plt.Circle((0, 0), r, fill=False, color=GRID, linewidth=0.5, alpha=0.3)
        ax.add_patch(circle)

    # --- Place entities ---
    n = len(entities)
    for i, e in enumerate(entities):
        name = e['entity']
        etype = e['type']
        trust = e['trust']
        connection = e['connection']
        intimacy = e['intimacy']
        respect = e['respect']
        alignment = e['alignment']
        power = e['power']
        impact = e['impact']

        # INTIMACY → distance from center (inverted: high intimacy = close)
        distance = 0.25 + (1.0 - intimacy) * 0.70  # range 0.25 to 0.95

        # Spread entities around the circle, but ALIGNMENT shifts Y
        # Base angle: evenly distribute
        base_angle = (2 * math.pi * i) / n - math.pi / 2  # start from top

        # Convert to x, y
        base_x = distance * math.cos(base_angle)
        base_y = distance * math.sin(base_angle)

        # ALIGNMENT nudges Y: high alignment pushes up, low pushes down
        # Scale: ±0.15 max nudge
        y_nudge = (alignment - 0.5) * 0.30
        x = base_x
        y = base_y + y_nudge

        # Clamp to bounds
        x = max(-1.05, min(1.05, x))
        y = max(-1.05, min(1.05, y))

        # IMPACT → font size (range 9 to 20)
        fontsize = 9 + impact * 11

        # RESPECT → text brightness/alpha
        alpha = 0.4 + respect * 0.6  # range 0.4 to 1.0

        # Type color
        color = TYPE_COLORS.get(etype, TEXT)

        # CONNECTION > 0.8 → line to center
        if connection > 0.8:
            ax.plot([0, x], [0, y], color=color, linewidth=1.5,
                    alpha=0.3, zorder=1)

        # CONNECTION → heart symbol behind text
        if connection > 0.5:
            heart_alpha = (connection - 0.5) * 1.0  # 0 to 0.5
            heart_size = 12 + connection * 8
            ax.text(x, y + 0.01, '♥', color=color, fontsize=heart_size,
                    ha='center', va='center', alpha=heart_alpha * 0.4, zorder=2)

        # TRUST → glow/highlight box behind text
        if trust > 0.3:
            glow_alpha = (trust - 0.3) * 0.5  # 0 to 0.35
            glow_width = len(name) * 0.022 + 0.04
            glow_height = 0.06
            glow = FancyBboxPatch((x - glow_width / 2, y - glow_height / 2),
                                   glow_width, glow_height,
                                   boxstyle="round,pad=0.02",
                                   facecolor=color, alpha=glow_alpha,
                                   edgecolor='none', zorder=3)
            ax.add_patch(glow)

        # Entity name
        ax.text(x, y, name, color=color, fontsize=fontsize,
                ha='center', va='center', fontweight='bold',
                alpha=alpha, zorder=5)

        # Type label below
        ax.text(x, y - 0.05, etype, color=MUTED, fontsize=7,
                ha='center', va='top', alpha=0.6, zorder=5)

    # --- Legend ---
    legend_y = -1.08
    ax.text(-1.10, legend_y, 'closer = intimate  |  higher = aligned  |  bigger = impact  |  brighter = respect  |  ♥ = connected  |  line = connection > 0.8',
            color=MUTED, fontsize=7.5, ha='left', va='top')

    # Type legend
    lx = 0.70
    for etype, color in TYPE_COLORS.items():
        ax.plot(lx, 1.10, 'o', color=color, markersize=5)
        ax.text(lx + 0.03, 1.10, etype, color=color, fontsize=8, va='center')
        lx += 0.22 if etype != 'object' else 0

    # Title
    ax.text(0, 1.10, 'HEART', color=ACCENT, fontsize=20,
            ha='center', va='center', fontweight='bold')

    # --- Save ---
    path = OUTPUT / 'heart_constellation.png'
    fig.savefig(path, dpi=120, facecolor=BG, bbox_inches='tight')
    plt.close(fig)
    return str(path)


if __name__ == '__main__':
    path = render_heart()
    if path:
        print(f'Constellation rendered to {path}')
    else:
        print('No entities in heart')
