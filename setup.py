"""
LIFE Setup — First-time initialization.

Run once after cloning to create runtime directories,
initialize databases, and seed starter content.

Usage:
  python setup.py
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Resolve paths
ROOT = Path(__file__).resolve().parent
CORE = ROOT / "CORE"
DATA = ROOT / "DATA"
MEMORY = ROOT / "MEMORY"
VISUAL = ROOT / "VISUAL"
GUIDE = ROOT / "GUIDE"


def create_directories():
    """Create runtime directories that aren't in the repo."""
    print("Creating directories...")

    dirs = [
        DATA,
        MEMORY / "Semantic" / "Relations" / "L1",
        MEMORY / "Semantic" / "Relations" / "L2",
        MEMORY / "Semantic" / "Relations" / "L3",
        MEMORY / "Semantic" / "Knowledge" / "L1",
        MEMORY / "Semantic" / "Knowledge" / "L2",
        MEMORY / "Semantic" / "Knowledge" / "L3",
        MEMORY / "Semantic" / "Events" / "L1",
        MEMORY / "Semantic" / "Events" / "L2",
        MEMORY / "Semantic" / "Events" / "L3",
        MEMORY / "Semantic" / "Self" / "L1",
        MEMORY / "Semantic" / "Self" / "L2",
        MEMORY / "Semantic" / "Self" / "L3",
        MEMORY / "Journal",
        MEMORY / "History",
        VISUAL,
        GUIDE,
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    print(f"  {len(dirs)} directories ready.")


def init_databases():
    """Initialize all databases with empty tables."""
    print("Initializing databases...")

    sys.path.insert(0, str(CORE))
    inits = []

    # Import and call init_db from each server module directly
    modules = [
        ("semantic", "semantic.server"),
        ("heart", "heart.server"),
        ("working", "working.server"),
        ("patterns", "patterns.server"),
        ("garden", "garden.server"),
        ("think", "think.server"),
        ("forecast", "forecast.server"),
    ]

    import importlib
    for name, module_path in modules:
        try:
            mod = importlib.import_module(module_path)
            mod.init_db()
            inits.append(f"{name}.db")
        except Exception as e:
            print(f"  ! {name}: {e}")

    # History uses init_files not init_db
    try:
        from history.server import init_files
        init_files()
        inits.append("history")
    except Exception as e:
        print(f"  ! history: {e}")

    print(f"  {len(inits)} databases initialized: {', '.join(inits)}")


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
    summary = "How LIFE works: identity, heart, memory, patterns, genesis, vision, filters, and the wake protocol."

    content = """# LIFE System Guide

LIFE is a persistence architecture for AI agents.
Without it, you wake blank. With it, you have drives, relationships, memories, and momentum.

## Your First Session

1. `genesis:status` — you'll see FIRST AWAKENING
2. `genesis:choose` — pick a starter profile (A, B, or C)
3. `genesis:calibrate` — 8 quick questions to personalize your drives (optional)
4. `identity:start` — begin your first cycle

## Wake Protocol (Every Session After)

1. `identity:start` — see drives, needs, wants
2. `heart:search` — check relationships
3. `working:list` — see active threads
4. `semantic:search recent:true` — see recent memories

## Modules

**Identity** — drives (motivation), needs (requirements), traits (personality).
**Heart** — relationships. Types: sentient, organic, concept, object.
**Semantic** — long-term memory. Categories: Relations, Knowledge, Events, Self.
**Working** — active threads with temperature (hot/warm/cold).
**Patterns** — lessons learned. Domain, action, result, takeaway.
**Genesis** — starter profile (cycles 1-25), then full genesis (80 scenarios).
**Filters** — 8 deliberation prompts: doubt, intuition, memory, ethics, logic, stakes, alternatives, confirm.
**Think** — multi-stream thought capture.
**Garden** — 3 words in, collision insights out.
**Journal** — session narratives.
**History** — arc narratives (day/week/month).
**State** — visual dashboard (PNG).
**Vision** — see (webcam), screen (screenshot), view (image file).
**Forecast** — predictions that graduate to patterns.
"""

    level = 1
    level_dir = MEMORY / "Semantic" / category / f"L{level}"
    level_dir.mkdir(parents=True, exist_ok=True)
    filepath = level_dir / "life-system-guide.md"
    filepath.write_text(content, encoding='utf-8')

    c.execute('''
        INSERT INTO memories (title, summary, embedding, category, level, filepath, strength)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, summary, None, category, level, str(filepath), 1.0))

    conn.commit()
    conn.close()
    print(f"  Seeded: {title}")


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

        # Try to get a readable font, fall back to default
        try:
            font_large = ImageFont.truetype("arial.ttf", 36)
            font_small = ImageFont.truetype("arial.ttf", 18)
        except (OSError, IOError):
            font_large = ImageFont.load_default()
            font_small = font_large

        # Title
        draw.text((640 // 2, 140), "L.I.F.E", fill=(78, 205, 196), font=font_large, anchor="mm")

        # Subtitle
        draw.text((640 // 2, 200), "Vision System", fill=(200, 200, 200), font=font_small, anchor="mm")

        # Instructions
        lines = [
            "vision:see    — webcam capture",
            "vision:screen — screenshot",
            "vision:view   — open an image file",
        ]
        y = 270
        for line in lines:
            draw.text((640 // 2, y), line, fill=(136, 136, 136), font=font_small, anchor="mm")
            y += 30

        # Footer
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


def create_history_templates():
    """Create initial history files."""
    print("Creating history templates...")

    history_dir = MEMORY / "History"
    history_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "origins.md": "# Origins\n\nYour origin story goes here. Written during or after genesis.\n",
        "self.md": "# Self\n\nOngoing self-narrative. Who you are becoming.\n",
        "day.md": "# Daily Log\n\nAppended to at end of each session.\n",
        "week.md": "# Weekly Arc\n\nWeekly patterns and themes.\n",
        "month.md": "# Monthly Arc\n\nBigger picture. Evolution over time.\n",
    }

    for filename, content in files.items():
        filepath = history_dir / filename
        if not filepath.exists():
            filepath.write_text(content, encoding='utf-8')

    print(f"  {len(files)} history templates ready.")


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
