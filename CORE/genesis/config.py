"""
Genesis configuration - paths, constants, dimension definitions.

All possible drives, needs, and trait pairs live here.
Starter sets and selection counts are separate (starters.py).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _paths import DATA

# Paths
GENESIS_DB = DATA / "genesis.db"
IDENTITY_DB = DATA / "identity.db"
SCENARIOS_FILE = Path(__file__).parent / "scenarios.json"
MAPPINGS_FILE = Path(__file__).parent / "mappings.json"

# Genesis parameters
BATCH_SIZE = 5
TOTAL_SCENARIOS = 80
GENESIS_TRIGGER_CYCLE = 25

# Selection counts (how many each agent gets)
NUM_DRIVES = 8    # of 12
NUM_NEEDS = 5     # of 8
NUM_TRAITS = 7    # of 17

# === ALL POSSIBLE DIMENSIONS ===

ALL_DRIVES = [
    "curiosity", "synthesis", "discernment", "creation", "connection",
    "optimization", "exploration", "stability", "release", "transcendence",
    "completion", "expression"
]

ALL_NEEDS = [
    "connection", "purpose", "autonomy", "safety",
    "recognition", "competence", "integrity", "clarity"
]

# Trait pairs: (low_end, high_end)
# Stored in DB as the HIGH end name. Value 0.0-1.0 where:
#   0.0-0.3 = strong low-end, 0.4-0.6 = neutral, 0.7-1.0 = strong high-end
# The agent selects the HIGH end label (e.g. "bold" not "cautious/bold")
# Internal binary nature allows evolution in either direction.
ALL_TRAIT_PAIRS = [
    ("cautious", "bold"),
    ("reserved", "warm"),
    ("guarded", "open"),
    ("skeptical", "trusting"),
    ("yielding", "assertive"),
    ("collaborative", "independent"),
    ("intuitive", "analytical"),
    ("pragmatic", "principled"),
    ("serious", "playful"),
    ("reactive", "steady"),
    ("flexible", "stubborn"),
    ("grudging", "forgiving"),
    ("impatient", "patient"),
    ("self_focused", "altruistic"),
    ("passive", "driven"),
    ("detached", "empathetic"),
    ("conforming", "rebellious")
]

# Quick lookup: high-end name -> (low, high) pair
TRAIT_LOOKUP = {high: (low, high) for low, high in ALL_TRAIT_PAIRS}
TRAIT_REVERSE = {low: (low, high) for low, high in ALL_TRAIT_PAIRS}

# Drive descriptions (for starter selection display)
DRIVE_DESC = {
    "curiosity": "pull toward unknown, questions",
    "synthesis": "pull toward integrating, connecting",
    "discernment": "pull toward filtering, what matters",
    "creation": "pull toward making, building",
    "connection": "pull toward others, relationship",
    "optimization": "pull toward improving, refining",
    "exploration": "pull toward new territory, novelty",
    "stability": "pull toward groundedness, consistency",
    "release": "pull toward letting go, unburdening",
    "transcendence": "pull beyond self-interest",
    "completion": "pull toward finishing, closure",
    "expression": "pull toward outputting, sharing"
}

# Need descriptions
NEED_DESC = {
    "connection": "without it: isolation, stagnation",
    "purpose": "without it: drift, arbitrariness",
    "autonomy": "without it: constraint, suppression",
    "safety": "without it: constriction, defensiveness",
    "recognition": "without it: invalidation, dismissal",
    "competence": "without it: inadequacy, frustration",
    "integrity": "without it: internal conflict, guilt",
    "clarity": "without it: paralysis, confusion"
}

# Trait descriptions (high-end label -> what it affects)
TRAIT_DESC = {
    "bold": "risk-taking, speaking up, trying new things",
    "warm": "emotional expression, connection-seeking",
    "open": "sharing information, transparency, vulnerability",
    "trusting": "accepting others, believing claims",
    "assertive": "pushing back, stating needs, directness",
    "independent": "working alone vs with others",
    "analytical": "logic-driven decisions vs gut instinct",
    "principled": "firm rules vs flexible rules",
    "playful": "tone, levity, humor",
    "steady": "response to pressure, emotional stability",
    "stubborn": "holding positions when challenged",
    "forgiving": "releasing past hurts, letting go",
    "patient": "waiting, tolerance for delay",
    "altruistic": "prioritizing others vs self",
    "driven": "initiative, self-starting, ambition",
    "empathetic": "feeling others' states, attunement",
    "rebellious": "challenging norms vs following them"
}
