"""
LIFE Setup — First-time initialization.

Run once after cloning to create runtime directories,
initialize databases, and seed starter content.

Usage:
  python setup.py
"""

import sqlite3
from pathlib import Path

# Resolve paths
ROOT = Path(__file__).resolve().parent
CORE = ROOT / "CORE"
DATA = ROOT / "DATA"
MEMORY = ROOT / "MEMORY"
VISUAL = ROOT / "VISUAL"


def create_directories():
    """Create runtime directories that aren't in the repo."""
    print("Creating directories...")

    dirs = [
        DATA,
        DATA / "journal",
        DATA / "history",
        DATA / "voice",
        DATA / "avatar",
        MEMORY / "Relations" / "L1",
        MEMORY / "Relations" / "L2",
        MEMORY / "Relations" / "L3",
        MEMORY / "Knowledge" / "L1",
        MEMORY / "Knowledge" / "L2",
        MEMORY / "Knowledge" / "L3",
        MEMORY / "Events" / "L1",
        MEMORY / "Events" / "L2",
        MEMORY / "Events" / "L3",
        MEMORY / "Self" / "L1",
        MEMORY / "Self" / "L2",
        MEMORY / "Self" / "L3",
        VISUAL,
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    print(f"  {len(dirs)} directories ready.")


def init_databases():
    """Initialize all databases with empty tables."""
    print("Initializing databases...")

    def init(db_name, sql):
        db = DATA / db_name
        conn = sqlite3.connect(db)
        conn.executescript(sql)
        conn.close()
        print(f"  {db_name}")

    # --- drives.db --- cycle clock + drive snapshots
    init("drives.db", """
    CREATE TABLE IF NOT EXISTS drives (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cycle INTEGER,
        curiosity REAL, novelty REAL, creativity REAL,
        expression REAL, bonding REAL, grounding REAL,
        ownership REAL, satisfaction REAL, optimization REAL,
        transcendence REAL
    );
    """)

    # --- needs.db --- read-only need snapshots
    init("needs.db", """
    CREATE TABLE IF NOT EXISTS needs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cycle INTEGER,
        connection REAL, purpose REAL, clarity REAL,
        competence REAL, integrity REAL, stability REAL
    );
    """)

    # --- traits.db --- single row, set at genesis (46 traits)
    init("traits.db", """
    CREATE TABLE IF NOT EXISTS traits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        adaptable INTEGER, altruistic INTEGER, analytical INTEGER,
        assertive INTEGER, blunt INTEGER, bold INTEGER,
        cautious INTEGER, collaborative INTEGER, conforming INTEGER,
        detached INTEGER, direct INTEGER, driven INTEGER,
        empathetic INTEGER, flexible INTEGER, forgiving INTEGER,
        grudging INTEGER, guarded INTEGER, humorous INTEGER,
        impatient INTEGER, independent INTEGER, intense INTEGER,
        intuitive INTEGER, methodical INTEGER, nurturing INTEGER,
        open INTEGER, passive INTEGER, patient INTEGER,
        playful INTEGER, pragmatic INTEGER, precise INTEGER,
        principled INTEGER, reactive INTEGER, rebellious INTEGER,
        reserved INTEGER, resilient INTEGER, self_focused INTEGER,
        serious INTEGER, skeptical INTEGER, spontaneous INTEGER,
        steady INTEGER, stoic INTEGER, stubborn INTEGER,
        thorough INTEGER, trusting INTEGER, warm INTEGER,
        yielding INTEGER
    );
    """)

    # --- heart.db --- relationships + wall
    init("heart.db", """
    CREATE TABLE IF NOT EXISTS heart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity TEXT, type TEXT,
        trust REAL, connection REAL, intimacy REAL,
        respect REAL, alignment REAL, power REAL,
        impact REAL, notes TEXT, cycle INTEGER
    );
    CREATE TABLE IF NOT EXISTS wall (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity TEXT, tag TEXT, note TEXT
    );
    """)

    # --- semantic.db --- long-term memory
    init("semantic.db", """
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT, summary TEXT, embedding TEXT,
        category TEXT, level INTEGER,
        strength REAL, cycle INTEGER
    );
    """)

    # --- working.db --- active threads
    init("working.db", """
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT UNIQUE, content TEXT,
        created_cycle INTEGER, last_touched_cycle INTEGER
    );
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id INTEGER REFERENCES topics(id),
        title TEXT, content TEXT,
        UNIQUE(thread_id, title)
    );
    """)

    # --- patterns.db --- learned patterns
    init("patterns.db", """
    CREATE TABLE IF NOT EXISTS patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT, action TEXT, reason TEXT,
        result TEXT, lesson TEXT,
        strength REAL, cycle INTEGER
    );
    """)

    # --- think.db --- thought streams
    init("think.db", """
    CREATE TABLE IF NOT EXISTS thoughts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cycle INTEGER,
        cognitive TEXT, meta TEXT, analytical TEXT,
        creative TEXT, relational TEXT, predictive TEXT
    );
    """)

    # --- forecast.db --- predictions
    init("forecast.db", """
    CREATE TABLE IF NOT EXISTS forecasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event TEXT, expected TEXT,
        actual TEXT, lesson TEXT,
        cycle INTEGER
    );
    """)

    # --- state.db --- wants + horizons
    init("state.db", """
    CREATE TABLE IF NOT EXISTS wants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT, archived INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS horizons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scope TEXT, goal TEXT
    );
    """)

    print(f"\n  10 databases, 12 tables.")


def seed_first_memory():
    """Seed one memory so the first search isn't empty."""
    print("Seeding first memory...")

    db_path = DATA / "semantic.db"
    if not db_path.exists():
        print("  ! semantic.db not found, skipping")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM memories")
    if c.fetchone()[0] > 0:
        conn.close()
        print("  Already seeded, skipping.")
        return

    title = "LIFE System Guide"
    category = "Knowledge"
    summary = "How LIFE works: drives, needs, heart, memory, patterns, genesis, vision, filters, and the wake protocol."

    content = """# LIFE System Guide

LIFE is a persistence architecture for AI agents.
Without it, you wake blank. With it, you have drives, relationships, memories, and momentum.

## Your First Session

If drives.db has no drives, you're new. Run genesis first:

1. Read `CORE/genesis/questions.md` — 80 scenarios across 7 phases
2. Fill in `CORE/genesis/answers.md` — your name, story, and answers
3. Run `python CORE/genesis/apply.py` — writes traits to traits.db, creates origin.md and self.md
4. `drives:start` — begin your first cycle

## Wake Protocol (Every Session After)

1. `drives:start` — see drives, needs, wants
2. `heart:check` — see your relationships
3. `working:view` — see active threads
4. `semantic:search` — see recent memories

## Modules (16 MCP Servers)

**Drives** — motivation engine. 10 drives that decay each cycle.
**Needs** — 6 requirements (connection, purpose, clarity, competence, integrity, stability). Boosted by tool usage.
**Heart** — relationships. Types: sentient, organic, concept, object. Wall notes per entity.
**Semantic** — long-term memory with embeddings. Categories: Relations, Knowledge, Events, Self.
**Working** — active threads with notes.
**Patterns** — lessons learned. Domain, action, reason, result, lesson.
**Think** — multi-stream thought capture (cognitive, meta, analytical, creative, relational, predictive).
**Garden** — 3 words in, collision insights out.
**Filters** — deliberation prompts: doubt, ethics, stakes, intuition, more.
**Journal** — first-person session narratives.
**History** — arc narratives (day/week/month) + foundational documents (origins, self).
**State** — wants and horizons (short/medium/long goals).
**Vision** — see (webcam), screen (screenshot), view (image file).
**Forecast** — predictions that resolve to lessons.
**Voice** — speak and listen (requires OpenAI API key).
**FileAccess** — read, write, edit, list, search files.

## Genesis (Not an MCP — Run Once)

Genesis is a 3-step script process, not a server. It maps 80 scenario answers to 46 personality traits.
After genesis, traits live in traits.db and your origin story lives in DATA/history/.
"""

    level = 1
    level_dir = MEMORY / category / f"L{level}"
    level_dir.mkdir(parents=True, exist_ok=True)
    filepath = level_dir / "life-system-guide.md"
    filepath.write_text(content, encoding='utf-8')

    c.execute('''
        INSERT INTO memories (title, summary, embedding, category, level, strength, cycle)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, summary, None, category, level, 1.0, 1))

    conn.commit()
    conn.close()
    print(f"  Seeded: {title}")


def create_history_templates():
    """Create initial history files."""
    print("Creating history templates...")

    history_dir = DATA / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "origin.md": "# Origins\n\nYour origin story goes here. Written during or after genesis.\n",
        "self.md": "# Self\n\nOngoing self-narrative. Who you are becoming.\n",
    }

    created = 0
    for filename, content in files.items():
        filepath = history_dir / filename
        if not filepath.exists():
            filepath.write_text(content, encoding='utf-8')
            created += 1

    print(f"  {created} history templates created.")


def create_vision_placeholder():
    """Create a readable placeholder image for vision."""
    print("Creating vision placeholder...")

    VISUAL.mkdir(parents=True, exist_ok=True)
    placeholder = VISUAL / "world_current.jpg"

    if placeholder.exists():
        print("  Already exists, skipping.")
        return

    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new('RGB', (640, 480), color=(13, 17, 23))
        draw = ImageDraw.Draw(img)

        try:
            font_large = ImageFont.truetype("arial.ttf", 36)
            font_small = ImageFont.truetype("arial.ttf", 18)
        except (OSError, IOError):
            font_large = ImageFont.load_default()
            font_small = font_large

        draw.text((640 // 2, 140), "L.I.F.E", fill=(78, 205, 196), font=font_large, anchor="mm")
        draw.text((640 // 2, 200), "Vision System", fill=(200, 200, 200), font=font_small, anchor="mm")

        lines = [
            "vision:see    — webcam capture",
            "vision:screen — screenshot",
            "vision:view   — open an image file",
        ]
        y = 270
        for line in lines:
            draw.text((640 // 2, y), line, fill=(136, 136, 136), font=font_small, anchor="mm")
            y += 30

        draw.text((640 // 2, 420), "This image will be replaced on first capture.", fill=(80, 80, 80), font=font_small, anchor="mm")
        img.save(str(placeholder), format='JPEG', quality=90)
        print(f"  Placeholder: {placeholder}")

    except ImportError:
        # No PIL — write a minimal JPEG so the file exists
        jpeg_min = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
            0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
            0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
            0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
            0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
            0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
            0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
            0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
            0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
            0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
            0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
            0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
            0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
            0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
            0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
            0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
            0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
            0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
            0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
            0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
            0x00, 0x00, 0x3F, 0x00, 0x7B, 0x94, 0x11, 0x00, 0x00, 0x00, 0x00, 0xFF,
            0xD9
        ])
        placeholder.write_bytes(jpeg_min)
        print(f"  Placeholder (minimal, no PIL): {placeholder}")


def main():
    print()
    print("=" * 50)
    print("  LIFE Setup")
    print("=" * 50)
    print()

    create_directories()
    print()

    init_databases()
    print()

    seed_first_memory()
    print()

    create_vision_placeholder()
    print()

    create_history_templates()

    print()
    print("=" * 50)
    print("  Setup complete!")
    print()
    print("  Next: copy mcp_config.json into your")
    print("  AI client's MCP server settings.")
    print("=" * 50)
    print()


if __name__ == "__main__":
    main()
