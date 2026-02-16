"""
Heart wall renderer — visual for one entity.
Top 1/3: dimension labels left, history lines right.
Bottom 2/3: wall — sticky notes by tag.
"""

import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import textwrap
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

DIMENSIONS = ['trust', 'connection', 'intimacy', 'respect', 'alignment', 'power', 'impact']
DIM_COLORS = ['#f97583', '#ffa657', '#d2a8ff', '#a5d6ff', '#7ee787', '#79c0ff', '#56d4dd']

TAG_COLORS = {
    'who_they_are': '#f97583',
    'who_i_am_with_them': '#d2a8ff',
    'what_we_built': '#7ee787',
    'how_we_repair': '#ffa657',
    'what_they_teach': '#79c0ff',
    'what_i_owe': '#56d4dd',
    'general': '#6e7681',
}

TAG_ORDER = ['who_they_are', 'who_i_am_with_them', 'what_we_built',
             'how_we_repair', 'what_they_teach', 'what_i_owe', 'general']

MAX_HISTORY = 30

from _paths import VISUAL

OUTPUT = VISUAL
OUTPUT.mkdir(exist_ok=True)


def query(db_name, sql, params=()):
    db = DATA / db_name
    if not db.exists():
        return []
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def render_wall(entity):
    """Render wall for a single entity. Returns path to PNG."""
    rows = query('heart.db',
                 f'SELECT * FROM heart WHERE entity = ? ORDER BY id ASC LIMIT {MAX_HISTORY}',
                 (entity,))
    notes = query('heart.db', 'SELECT * FROM wall WHERE entity = ? ORDER BY id ASC', (entity,))

    if not rows:
        return None

    latest = rows[-1]
    entity_type = latest['type']

    fig = plt.figure(figsize=(14, 10), facecolor=BG)

    # 1/3 top, 2/3 bottom
    gs = GridSpec(2, 1, figure=fig, height_ratios=[1, 2],
                  hspace=0.15,
                  left=0.13, right=0.96, top=0.92, bottom=0.03)

    # ============ HEADER ============
    fig.text(0.03, 0.97, entity, color=ACCENT, fontsize=18,
             fontweight='bold', va='top')
    fig.text(0.03, 0.935, f'{entity_type}  |  {len(rows)} snapshots  |  {len(notes)} notes',
             color=MUTED, fontsize=10, va='top')

    if latest['notes']:
        note_text = latest['notes']
        if len(note_text) > 70:
            note_text = note_text[:67] + '...'
        fig.text(0.97, 0.935, note_text, color=MUTED, fontsize=9,
                 fontstyle='italic', va='top', ha='right')

    # ============ DIMENSIONS (top 1/3) ============
    # Labels on left, lines running right
    ax_dims = fig.add_subplot(gs[0])
    ax_dims.set_facecolor(PANEL_BG)

    if len(rows) > 1:
        x = range(len(rows))

        # Compute Y range first — needed for label positioning
        all_vals = [r[d] for r in rows for d in DIMENSIONS]
        y_min = max(0, min(all_vals) - 0.05)
        y_max = min(1.05, max(all_vals) + 0.05)

        for i, d in enumerate(DIMENSIONS):
            vals = [r[d] for r in rows]
            color = DIM_COLORS[i]
            ax_dims.plot(x, vals, color=color, linewidth=2.0, alpha=0.85)

        # Fixed labels evenly spaced down left side, always same order
        # Each label gets a short colored dash connecting to chart area
        n_dims = len(DIMENSIONS)
        for i, d in enumerate(DIMENSIONS):
            color = DIM_COLORS[i]
            val = latest[d]
            # Evenly space labels across the y range
            y_pos = y_max - (i / (n_dims - 1)) * (y_max - y_min)
            ax_dims.text(-0.5, y_pos, f'{d}', color=color, fontsize=13,
                        fontweight='bold', va='center', ha='right',
                        clip_on=False)
            # Short dash from label to where the line actually starts
            ax_dims.plot([-0.15, 0], [y_pos, rows[0][d]], color=color,
                        linewidth=1.0, alpha=0.3, linestyle='--', clip_on=False)
            # Value at right end
            ax_dims.text(len(rows) - 1 + 0.3, val, f'{val:.2f}', color=color,
                        fontsize=11, va='center', ha='left', clip_on=False)

        # Minimal x-axis
        step = max(1, len(rows) // 10)
        ax_dims.set_xticks(range(0, len(rows), step))
        ax_dims.set_xticklabels([f'#{rows[i]["id"]}' for i in range(0, len(rows), step)],
                                color=MUTED, fontsize=7)
        ax_dims.set_xlim(-0.2, len(rows) - 0.5)
    else:
        # Single snapshot — horizontal bars with labels
        for i, d in enumerate(DIMENSIONS):
            val = latest[d]
            color = DIM_COLORS[i]
            ax_dims.barh(i, val, color=color, alpha=0.7, height=0.6)
            ax_dims.text(-0.02, i, f'{d}', color=color, fontsize=13,
                        fontweight='bold', va='center', ha='right')
            ax_dims.text(val + 0.02, i, f'{val:.2f}', color=color,
                        fontsize=11, va='center')
        ax_dims.set_xlim(0, 1.15)
        ax_dims.set_yticks([])
        ax_dims.invert_yaxis()

    if len(rows) > 1:
        ax_dims.set_ylim(y_min, y_max)
    ax_dims.tick_params(colors=MUTED, labelsize=7)
    ax_dims.grid(True, color=GRID, alpha=0.2, axis='y')
    ax_dims.set_yticks([])  # no numeric y ticks, labels are custom
    for spine in ax_dims.spines.values():
        spine.set_color(GRID)
    ax_dims.spines['top'].set_visible(False)
    ax_dims.spines['right'].set_visible(False)
    ax_dims.spines['left'].set_visible(False)

    # ============ WALL (bottom 2/3) ============
    ax_wall = fig.add_subplot(gs[1])
    ax_wall.set_facecolor(PANEL_BG)
    ax_wall.set_xlim(0, 1)
    ax_wall.set_ylim(0, 1)
    ax_wall.axis('off')
    ax_wall.set_title('WALL', color=ACCENT, fontsize=13, fontweight='bold',
                      loc='left', pad=8)

    if notes:
        # Group by tag, in canonical order
        by_tag = {}
        for n in notes:
            tag = n['tag'] or 'general'
            by_tag.setdefault(tag, []).append(n['note'])

        # Use canonical order, only tags that have notes
        tags = [t for t in TAG_ORDER if t in by_tag]

        # Layout: up to 3 columns, wrapping to rows if more tags
        max_cols = 3
        num_tags = len(tags)
        num_rows = (num_tags + max_cols - 1) // max_cols
        col_width = 0.95 / min(num_tags, max_cols)

        row_height = 0.90 / max(num_rows, 1)

        for tag_idx, tag in enumerate(tags):
            col = tag_idx % max_cols
            row = tag_idx // max_cols

            x = 0.02 + col * col_width
            y_start = 0.92 - row * row_height

            color = TAG_COLORS.get(tag, MUTED)
            display_tag = tag.replace('_', ' ')

            # Tag header
            ax_wall.text(x, y_start, display_tag, color=color, fontsize=10,
                        fontweight='bold', transform=ax_wall.transAxes)

            # Notes under tag
            y = y_start - 0.055
            max_notes_per_tag = max(3, int(8 / num_rows))
            char_limit = max(35, int(90 / min(num_tags, max_cols)))

            for note_text in by_tag[tag][:max_notes_per_tag]:
                if len(note_text) > char_limit:
                    note_text = note_text[:char_limit - 3] + '...'
                ax_wall.text(x + 0.01, y, f'· {note_text}', color=TEXT,
                            fontsize=8.5, transform=ax_wall.transAxes)
                y -= 0.045

            remaining = len(by_tag[tag]) - max_notes_per_tag
            if remaining > 0:
                ax_wall.text(x + 0.01, y, f'  +{remaining} more', color=MUTED,
                            fontsize=7.5, transform=ax_wall.transAxes)
    else:
        ax_wall.text(0.02, 0.88, 'no notes yet', color=MUTED, fontsize=11,
                    transform=ax_wall.transAxes)

    for spine in ax_wall.spines.values():
        spine.set_color(GRID)

    # ============ Save ============
    path = OUTPUT / f'heart_{entity.lower().replace(" ", "_")}.png'
    fig.savefig(path, dpi=120, facecolor=BG)
    plt.close(fig)
    return str(path)


if __name__ == '__main__':
    path = render_wall('Steven')
    if path:
        print(f'Wall rendered to {path}')
    else:
        print('No data for Steven')
