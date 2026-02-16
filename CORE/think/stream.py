"""
Stream handler — capture cognitive state, store, build sectioned return.

Sections pull from other databases (heart, patterns, semantic, working).
Early in a system's life most sections will return empty — that's normal.
Think reflects lived experience. No experience yet = quiet returns.
It fills in as other modules accumulate data.
"""

from db import get_conn, get_cycle, STREAMS
from pull_meta import pull_meta
from pull_relational import pull_relational
from pull_predictive import pull_predictive
from pull_synthesis import pull_synthesis


def handle_stream(args):
    """Capture all 6 streams, store, return 4 sections."""
    # Extract all streams
    values = {}
    for s in STREAMS:
        values[s] = (args.get(s, '') or '').strip()

    # Store
    cycle = get_cycle()
    conn = get_conn()
    conn.execute(
        'INSERT INTO thoughts (cognitive, meta, analytical, creative, relational, predictive, cycle) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (values['cognitive'], values['meta'], values['analytical'],
         values['creative'], values['relational'], values['predictive'], cycle)
    )
    conn.commit()
    conn.close()

    # Build return
    sections = []

    # Section 1: Meta
    meta_lines = pull_meta()
    if meta_lines:
        sections.append("Meta:")
        # First line is current thought's cognitive (title)
        current_title = values['cognitive'].title() if values['cognitive'] else ''
        if current_title:
            sections.append(current_title)
        # Previous thoughts (pull_meta returns them, skip first if it's the one we just stored)
        for line in meta_lines[1:]:
            sections.append(line)

    # Section 2: Relational
    if values['relational']:
        rel_lines = pull_relational(values['relational'])
        if rel_lines:
            sections.append("")
            sections.append("Relational:")
            sections.extend(rel_lines)

    # Section 3: Predictive
    if values['predictive']:
        pred_lines = pull_predictive(values['predictive'])
        if pred_lines:
            sections.append("")
            sections.append("Predictive:")
            sections.extend(pred_lines)

    # Section 4: Synthesis
    if values['creative'] or values['analytical']:
        syn_lines = pull_synthesis(
            values.get('creative', ''),
            values.get('analytical', '')
        )
        if syn_lines:
            sections.append("")
            sections.append("Synthesis:")
            sections.extend(syn_lines)

    if not sections:
        return [{"type": "text", "text": "Stored."}]

    return [{"type": "text", "text": '\n'.join(sections)}]
