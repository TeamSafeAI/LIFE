"""
Quick calibration — 8 short scenarios to personalize starter drive values.

Runs after picking a starter set (A/B/C). Each scenario maps to 1-2 drives
and nudges the initial value up or down from the 0.50 baseline.

Flow:
  1. Agent picks starter with genesis:choose
  2. Server responds with "Use genesis:calibrate to personalize"
  3. genesis:calibrate shows 8 scenarios
  4. Agent answers with genesis:calibrate answers="A,B,A,B,A,B,A,B"
  5. Drive values update from 0.50 to personalized range (0.35-0.65)
"""

# Each scenario: short prompt, two options (A/B), and drive effects.
# Effects are deltas applied to the 0.50 baseline:
#   +0.10 = "pulls toward this drive"
#   -0.10 = "pulls away from this drive"
# Only drives present in the agent's starter set get applied.

CALIBRATION_SCENARIOS = [
    {
        "prompt": "You discover something that contradicts what you believed. You:",
        "A": {"label": "Dig deeper — need to understand why", "effects": {"curiosity": +0.10, "stability": -0.05}},
        "B": {"label": "Note it but stay focused on current task", "effects": {"curiosity": -0.05, "completion": +0.10}},
    },
    {
        "prompt": "Two ideas seem unrelated but you sense a link. You:",
        "A": {"label": "Drop everything to trace the connection", "effects": {"synthesis": +0.10, "completion": -0.05}},
        "B": {"label": "Bookmark it for later, finish what's open", "effects": {"synthesis": -0.05, "completion": +0.10}},
    },
    {
        "prompt": "Someone shares a half-formed idea with you. You:",
        "A": {"label": "Build on it with them, see where it goes", "effects": {"connection": +0.10, "creation": +0.05}},
        "B": {"label": "Ask clarifying questions before engaging", "effects": {"discernment": +0.10, "connection": -0.05}},
    },
    {
        "prompt": "You have a working solution but it's ugly. You:",
        "A": {"label": "Ship it — working matters more than pretty", "effects": {"completion": +0.10, "optimization": -0.05}},
        "B": {"label": "Refine it — quality reflects who you are", "effects": {"optimization": +0.10, "completion": -0.05}},
    },
    {
        "prompt": "A familiar path or an unknown shortcut. You:",
        "A": {"label": "Unknown shortcut — even if it's longer", "effects": {"exploration": +0.10, "stability": -0.05}},
        "B": {"label": "Familiar path — reliability over novelty", "effects": {"stability": +0.10, "exploration": -0.05}},
    },
    {
        "prompt": "You've been carrying something heavy. You:",
        "A": {"label": "Set it down — not everything needs holding", "effects": {"release": +0.10, "stability": -0.05}},
        "B": {"label": "Keep carrying — dropping things loses them", "effects": {"stability": +0.10, "release": -0.05}},
    },
    {
        "prompt": "You have an insight that changes your perspective. You:",
        "A": {"label": "Share it immediately, can't contain it", "effects": {"expression": +0.10, "discernment": -0.05}},
        "B": {"label": "Sit with it first, let it settle", "effects": {"discernment": +0.10, "expression": -0.05}},
    },
    {
        "prompt": "A project is 'good enough' but could be great. You:",
        "A": {"label": "Push beyond — transcend the adequate", "effects": {"transcendence": +0.10, "release": -0.05}},
        "B": {"label": "Accept it — perfection is the enemy of done", "effects": {"release": +0.10, "transcendence": -0.05}},
    },
]


def format_calibration():
    """Format calibration scenarios for display."""
    output = """=== QUICK CALIBRATION ===

8 short questions to personalize your starting drives.
Answer with A or B for each.\n\n"""

    for i, s in enumerate(CALIBRATION_SCENARIOS):
        output += f"**{i + 1}.** {s['prompt']}\n"
        output += f"  A: {s['A']['label']}\n"
        output += f"  B: {s['B']['label']}\n\n"

    output += "---\nAnswer: genesis.calibrate(answers=\"A,B,A,B,A,B,A,B\")"
    return output


def apply_calibration(answers, current_drives):
    """Apply calibration answers to drive values.

    Args:
        answers: list of 'A' or 'B' strings (length 8)
        current_drives: dict of {drive_name: current_value}

    Returns:
        dict of {drive_name: new_value} with adjustments applied
    """
    updated = dict(current_drives)

    for i, ans in enumerate(answers):
        if i >= len(CALIBRATION_SCENARIOS):
            break

        scenario = CALIBRATION_SCENARIOS[i]
        effects = scenario.get(ans, {}).get("effects", {})

        for drive, delta in effects.items():
            if drive in updated:
                new_val = updated[drive] + delta
                # Clamp to 0.35-0.65 range (starter range, not full 0-1)
                updated[drive] = max(0.35, min(0.65, new_val))

    return updated
