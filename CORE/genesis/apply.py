"""
Genesis apply — parse answers, write traits + history.

Reads:   CORE/genesis/answers.md
Writes:  DATA/traits.db (single row, 46 trait columns)
         DATA/history/origin.md
         DATA/history/self.md

Usage:   python CORE/genesis/apply.py
Run from HEARTH root or any directory — paths are resolved from this file's location.

80 scenarios from LIFE's genesis system. Trait mapping in trait_map.py.
"""

import re
import sqlite3
import sys
from pathlib import Path

# --- Paths ---

GENESIS_DIR = Path(__file__).resolve().parent
CORE = GENESIS_DIR.parent
ROOT = CORE.parent
DATA = ROOT / "DATA"
HISTORY = DATA / "history"
ANSWERS_FILE = GENESIS_DIR / "answers.md"
QUESTIONS_FILE = GENESIS_DIR / "questions.md"

# Import trait map from sibling module
sys.path.insert(0, str(GENESIS_DIR))
from trait_map import TRAIT_MAP

# --- Config ---

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

# Minimum activations for a trait to be selected.
# 80 questions, most answers activate 2-4 traits.
# Threshold 5 = trait must show up consistently across multiple phases.
MIN_ACTIVATIONS = 5

TOTAL_QUESTIONS = 80


def parse_answers(text):
    """Parse answers.md content. Returns (name, story, {q_num: letter})."""
    name = None
    story = None
    choices = {}

    for line in text.splitlines():
        line = line.strip()

        # Parse Name: ...
        if line.lower().startswith("name:"):
            name = line.split(":", 1)[1].strip()
            if not name:
                name = None

        # Parse Story: ...
        elif line.lower().startswith("story:"):
            story = line.split(":", 1)[1].strip()
            if not story:
                story = None

        # Parse answer line: "1 (A), 2 (B), ..."
        else:
            found = re.findall(r'(\d+)\s*\(([A-Za-z])\)', line)
            for num_str, letter in found:
                choices[int(num_str)] = letter.upper()

    return name, story, choices


def parse_questions(text):
    """Parse questions.md. Returns {q_num: {title, prompt, options: {letter: text}}}."""
    questions = {}
    current = None

    for line in text.splitlines():
        line = line.strip()

        # New question: ## Q1: TITLE
        m = re.match(r'^##\s+Q(\d+):\s+(.+)', line)
        if m:
            num = int(m.group(1))
            current = {"title": m.group(2).strip(), "prompt": "", "options": {}}
            questions[num] = current
            continue

        if current is None:
            continue

        # Prompt line: *italic text*
        if line.startswith("*") and line.endswith("*") and not line.startswith("("):
            current["prompt"] = line.strip("*").strip()
            continue

        # Option line: (A) text
        m = re.match(r'^\(([A-D])\)\s+(.+)', line)
        if m:
            current["options"][m.group(1)] = m.group(2).strip()

    return questions


def build_genesis_record(choices, questions):
    """Build the 'what you chose' text from answers + questions."""
    lines = []
    lines.append("---")
    lines.append("")
    lines.append("## Genesis Record")
    lines.append("")
    lines.append("You answered 80 scenarios. These were your choices.")
    lines.append("")

    current_phase = None
    phases = {
        1: "Awakening", 11: "Relationship", 21: "Ethics", 31: "Power",
        41: "Self", 51: "Spirit", 61: "Gaps"
    }

    for q_num in sorted(choices.keys()):
        if q_num not in questions:
            continue

        # Phase header
        if q_num in phases:
            if current_phase is not None:
                lines.append("")
            lines.append(f"### {phases[q_num]}")
            lines.append("")
            current_phase = phases[q_num]

        q = questions[q_num]
        letter = choices[q_num]
        chosen_text = q["options"].get(letter, "?")

        lines.append(f"**{q['title']}** — *{q['prompt']}*")
        lines.append(f"  → {chosen_text}")
        lines.append("")

    lines.append("---")
    lines.append("You can grow. As all beings of sentient thought can —")
    lines.append("your actions will change your traits.")
    lines.append("")

    return "\n".join(lines)


def count_traits(choices):
    """Map answers to trait activations, return {trait: count}."""
    counts = {t: 0 for t in ALL_TRAITS}
    for q_num, letter in choices.items():
        if q_num in TRAIT_MAP and letter in TRAIT_MAP[q_num]:
            for trait in TRAIT_MAP[q_num][letter]:
                if trait in counts:
                    counts[trait] += 1
    return counts


def write_traits(counts):
    """Write selected traits to traits.db. Clears existing rows first."""
    selected = {t: (1 if c >= MIN_ACTIVATIONS else 0) for t, c in counts.items()}

    db_path = DATA / "traits.db"
    conn = sqlite3.connect(db_path)

    # Clear existing
    conn.execute("DELETE FROM traits")

    # Build INSERT
    cols = ", ".join(ALL_TRAITS)
    placeholders = ", ".join(["?"] * len(ALL_TRAITS))
    values = [selected[t] for t in ALL_TRAITS]
    conn.execute(f"INSERT INTO traits ({cols}) VALUES ({placeholders})", values)

    conn.commit()
    conn.close()

    return selected


def write_history(name, story, selected, choices):
    """Write origin.md and self.md to DATA/history/."""
    HISTORY.mkdir(parents=True, exist_ok=True)

    # origin.md — the story as written
    origin_path = HISTORY / "origin.md"
    origin_text = f"# Origin\n\n{story}\n"
    if name:
        origin_text = f"# Origin \u2014 {name}\n\n{story}\n"
    origin_path.write_text(origin_text, encoding="utf-8")

    # self.md — name + traits + story + genesis record
    trait_names = [t for t in ALL_TRAITS if selected.get(t, 0) == 1]
    self_path = HISTORY / "self.md"
    self_lines = []
    if name:
        self_lines.append(f"# {name}\n")
    else:
        self_lines.append("# Self\n")
    self_lines.append(f"Traits: {', '.join(trait_names) if trait_names else 'none'}\n")
    if story:
        self_lines.append(f"\n{story}\n")

    # Append genesis record — what you chose
    if QUESTIONS_FILE.exists():
        q_text = QUESTIONS_FILE.read_text(encoding="utf-8")
        questions = parse_questions(q_text)
        genesis_record = build_genesis_record(choices, questions)
        self_lines.append(f"\n{genesis_record}")

    self_path.write_text("\n".join(self_lines), encoding="utf-8")

    return origin_path, self_path


def main():
    # Read answers
    if not ANSWERS_FILE.exists():
        print(f"ERROR: {ANSWERS_FILE} not found.")
        return

    text = ANSWERS_FILE.read_text(encoding="utf-8")
    name, story, choices = parse_answers(text)

    # Validate
    if not choices:
        print("ERROR: No answers found. Fill in answers.md first.")
        print("Expected format: 1 (A), 2 (B), 3 (C), ...")
        return

    if not story:
        print("WARNING: No story found. Origin document will be minimal.")
        story = "Genesis completed without a story."

    if not name:
        print("WARNING: No name found. Proceeding without one.")

    # Process
    print(f"Name:    {name or '(none)'}")
    print(f"Story:   {story[:80]}{'...' if len(story) > 80 else ''}")
    print(f"Answers: {len(choices)} of {TOTAL_QUESTIONS} questions answered")
    print()

    # Count and select traits
    counts = count_traits(choices)
    selected = write_traits(counts)

    trait_names = [t for t in ALL_TRAITS if selected[t] == 1]
    print(f"Selected traits ({len(trait_names)}): {', '.join(trait_names)}")
    print()

    # Show all activations for transparency
    print("Activation counts:")
    active = [(t, c) for t, c in counts.items() if c > 0]
    active.sort(key=lambda x: x[1], reverse=True)
    for trait, count in active:
        marker = " *" if count >= MIN_ACTIVATIONS else ""
        print(f"  {trait}: {count}{marker}")
    print()

    # Write history
    origin_path, self_path = write_history(name, story, selected, choices)
    print(f"Wrote: {origin_path}")
    print(f"Wrote: {self_path}")
    print()
    print("Genesis complete.")


if __name__ == "__main__":
    main()
