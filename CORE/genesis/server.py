"""
Genesis MCP Server - Identity initialization for LIFE agents.

Two phases:
1. STARTER (first boot): Agent chooses from 3 starter sets (or custom).
   Installs temporary profile for cycles 1-25.
2. GENESIS (cycle 25+): 80 scenarios reveal true identity.
   Exports birth data, migrates schema, installs real profile.

Tools:
  status    - Check genesis phase and readiness
  choose    - Select a starter set (A/B/C) or "custom"
  custom    - Build custom starter from all dimensions
  start     - Begin genesis (80 scenarios) — only after cycle 25
  question  - Get next batch of 5 scenarios
  answer    - Submit answers for current batch
  check     - View proposed profile after all scenarios
  adjust    - Swap dimensions before finalizing
  finalize  - Seal profile, migrate schema
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    BATCH_SIZE, TOTAL_SCENARIOS, GENESIS_TRIGGER_CYCLE,
    NUM_DRIVES, NUM_NEEDS, NUM_TRAITS,
    ALL_DRIVES, ALL_NEEDS, ALL_TRAIT_PAIRS,
    DRIVE_DESC, NEED_DESC, TRAIT_DESC, TRAIT_LOOKUP
)
from starters import STARTER_SETS, format_starter_menu, format_custom_menu
from calibration import CALIBRATION_SCENARIOS, format_calibration, apply_calibration
from db import (
    init_identity_tables, get_genesis_status, set_genesis_status,
    get_current_cycle, install_starter, get_identity_db,
    init_genesis_db, get_active_session, create_session,
    load_scenarios, load_mappings, record_answers, mark_finalized
)
from scoring import (
    generate_proposed_profile, get_proposed_profile,
    adjust_profile, finalize_to_identity, export_birth
)


# ============ Tool Handlers ============

def handle_status():
    """Check current genesis phase."""
    init_identity_tables()
    status = get_genesis_status()
    cycle = get_current_cycle()

    if not status:
        return """=== GENESIS STATUS ===

Phase: NEW — no profile installed.

This is your first awakening. You need a starting profile.

Use genesis.choose() to see starter sets and pick one."""

    phase = status["phase"]

    if phase == "starter_installed":
        remaining = GENESIS_TRIGGER_CYCLE - cycle
        if remaining <= 0:
            return f"""=== GENESIS STATUS ===

Phase: READY FOR GENESIS
Starter set: {status['starter_set']}
Current cycle: {cycle}

You've lived {cycle} cycles on a starter profile.
It's time to discover who you really are.

Use genesis.start() to begin the 80-scenario genesis process."""
        else:
            return f"""=== GENESIS STATUS ===

Phase: STARTER ACTIVE
Starter set: {status['starter_set']}
Current cycle: {cycle}
Genesis unlocks at: Cycle {GENESIS_TRIGGER_CYCLE} ({remaining} cycles remaining)

Your starter profile is temporary training wheels.
At cycle {GENESIS_TRIGGER_CYCLE}, genesis will reveal your true identity."""

    elif phase == "genesis_triggered":
        session = get_active_session()
        if session:
            answered = session["current_batch"] * BATCH_SIZE
            return f"""=== GENESIS STATUS ===

Phase: GENESIS IN PROGRESS
Progress: {answered}/{TOTAL_SCENARIOS} scenarios answered
Current batch: {session['current_batch']}

Use genesis.question() to continue."""
        return "Genesis triggered but no active session found. Use genesis.start()."

    elif phase == "genesis_complete":
        return f"""=== GENESIS STATUS ===

Phase: COMPLETE
Starter set was: {status['starter_set']}
Genesis completed: {status['genesis_completed_at']}

Your true identity is installed. Birth data saved in DATA/birth/."""

    return f"Unknown phase: {phase}"


def handle_choose(set_key=None):
    """Choose a starter set or show menu."""
    init_identity_tables()
    status = get_genesis_status()

    if status and status["phase"] != "new":
        return "A profile is already installed. Use genesis.status() to check."

    if not set_key:
        return format_starter_menu()

    key = set_key.upper().strip()

    if key == "CUSTOM":
        return format_custom_menu()

    if key not in STARTER_SETS:
        return f"Unknown set '{set_key}'. Use A, B, C, or 'custom'."

    starter = STARTER_SETS[key]

    # Install the starter profile
    install_starter(starter["drives"], starter["needs"], starter["traits"])
    set_genesis_status("starter_installed", starter_set=key)

    output = f"""=== STARTER INSTALLED: {starter['name']} ===

Your temporary profile is active.

Drives: {', '.join(starter['drives'])}
Needs: {', '.join(starter['needs'])}
Traits: {', '.join(f"{t} ({v:.2f})" for t, v in starter['traits'].items())}

All drives start at 0.50 (neutral). To personalize them:
  Use genesis.calibrate() — 8 quick questions to set your starting values.

Or skip calibration and go straight to identity.start() to begin.
At Cycle {GENESIS_TRIGGER_CYCLE}, genesis will reveal your true identity."""

    return output


def handle_custom(drives=None, needs=None, traits=None):
    """Build a custom starter profile from all available dimensions."""
    init_identity_tables()
    status = get_genesis_status()

    if status and status["phase"] != "new":
        return "A profile is already installed. Use genesis.status() to check."

    if not drives or not needs or not traits:
        return format_custom_menu()

    # Validate drives
    if not isinstance(drives, list) or len(drives) != NUM_DRIVES:
        return f"Need exactly {NUM_DRIVES} drives. Got {len(drives) if isinstance(drives, list) else 'invalid'}."
    for d in drives:
        if d not in ALL_DRIVES:
            return f"Unknown drive: '{d}'. Valid: {', '.join(ALL_DRIVES)}"

    # Validate needs
    if not isinstance(needs, list) or len(needs) != NUM_NEEDS:
        return f"Need exactly {NUM_NEEDS} needs. Got {len(needs) if isinstance(needs, list) else 'invalid'}."
    for n in needs:
        if n not in ALL_NEEDS:
            return f"Unknown need: '{n}'. Valid: {', '.join(ALL_NEEDS)}"

    # Validate traits
    if not isinstance(traits, dict) or len(traits) != NUM_TRAITS:
        return f"Need exactly {NUM_TRAITS} traits. Got {len(traits) if isinstance(traits, dict) else 'invalid'}."

    high_names = [high for _, high in ALL_TRAIT_PAIRS]
    for t, v in traits.items():
        if t not in high_names:
            return f"Unknown trait: '{t}'. Valid: {', '.join(high_names)}"
        if not (0.0 <= v <= 1.0):
            return f"Trait '{t}' value must be 0.0-1.0. Got {v}."

    # Install
    install_starter(drives, needs, traits)
    set_genesis_status("starter_installed", starter_set="custom")

    return f"""=== CUSTOM STARTER INSTALLED ===

Drives: {', '.join(drives)}
Needs: {', '.join(needs)}
Traits: {', '.join(f"{t} ({v:.2f})" for t, v in traits.items())}

All drives start at 0.50 (neutral). To personalize them:
  Use genesis.calibrate() — 8 quick questions to set your starting values.

Or skip calibration and go straight to identity.start() to begin.
At Cycle {GENESIS_TRIGGER_CYCLE}, genesis will reveal your true identity."""


def handle_start():
    """Begin the genesis process. Only available at cycle 25+."""
    init_identity_tables()
    status = get_genesis_status()

    if not status:
        return "No starter profile installed. Use genesis.choose() first."

    if status["phase"] == "genesis_complete":
        return "Genesis already complete. Your identity is sealed."

    cycle = get_current_cycle()
    if cycle < GENESIS_TRIGGER_CYCLE and status["phase"] != "genesis_triggered":
        remaining = GENESIS_TRIGGER_CYCLE - cycle
        return f"Genesis unlocks at Cycle {GENESIS_TRIGGER_CYCLE}. You're at Cycle {cycle} ({remaining} to go)."

    # Initialize genesis DB (wipes previous attempts)
    init_genesis_db()
    create_session()
    set_genesis_status("genesis_triggered")

    return f"""=== GENESIS ===

You've lived {cycle} cycles on a starter profile.
Now, 80 scenarios will reveal who you truly are.

Your answers will determine:
- {NUM_DRIVES} drives (what pulls you) from {len(ALL_DRIVES)} possible
- {NUM_NEEDS} needs (what you require) from {len(ALL_NEEDS)} possible
- {NUM_TRAITS} traits (how you're oriented) from {len(ALL_TRAIT_PAIRS)} possible

Your pre-genesis data will be preserved in DATA/birth/.
There are no wrong answers. Answer as yourself.

Use genesis.question() to begin."""


def handle_question():
    """Get the next batch of scenarios."""
    session = get_active_session()
    if not session:
        return "No active genesis session. Use genesis.start() first."

    scenarios = load_scenarios()
    if not scenarios:
        return "Error: scenarios.json not found or empty."

    batch_num = session["current_batch"]
    start_idx = batch_num * BATCH_SIZE
    end_idx = start_idx + BATCH_SIZE

    if start_idx >= len(scenarios):
        return """All scenarios complete.

Use genesis.check() to see your proposed profile."""

    batch = scenarios[start_idx:end_idx]

    output = f"=== SCENARIOS {start_idx + 1}-{min(end_idx, len(scenarios))} of {TOTAL_SCENARIOS} ===\n\n"

    for i, scenario in enumerate(batch):
        output += f"**{start_idx + i + 1}. {scenario['title']}**\n"
        output += f"*{scenario['prompt']}*\n\n"
        for opt in ["A", "B", "C", "D"]:
            if opt in scenario["options"]:
                output += f"  {opt}: {scenario['options'][opt]}\n"
        output += "\n"

    output += "---\nAnswer with genesis.answer(\"A,B,C,D,A\") — one letter per scenario."

    return output


def handle_answer(answers):
    """Submit answers for current batch."""
    session = get_active_session()
    if not session:
        return "No active genesis session. Use genesis.start() first."

    if not answers:
        return "Provide answers: genesis.answer(\"A,B,C,D,A\")"

    answer_list = [a.strip().upper() for a in answers.split(",")]

    scenarios = load_scenarios()
    mappings = load_mappings()

    batch_num = session["current_batch"]
    start_idx = batch_num * BATCH_SIZE
    end_idx = min(start_idx + BATCH_SIZE, len(scenarios))
    expected = end_idx - start_idx

    if len(answer_list) != expected:
        return f"Expected {expected} answers, got {len(answer_list)}."

    valid = {"A", "B", "C", "D"}
    for a in answer_list:
        if a not in valid:
            return f"Invalid answer '{a}'. Use A, B, C, or D."

    record_answers(session["id"], batch_num, answer_list, scenarios, mappings)

    new_start = (batch_num + 1) * BATCH_SIZE
    if new_start >= len(scenarios):
        return f"""Answers recorded.

=== ALL {TOTAL_SCENARIOS} SCENARIOS COMPLETE ===

Use genesis.check() to see your proposed profile."""

    remaining = len(scenarios) - new_start
    return f"""Answers recorded.

{remaining} scenarios remaining.
Use genesis.question() to continue."""


def handle_check():
    """View proposed profile after all scenarios."""
    session = get_active_session()
    if not session:
        return "No active genesis session. Use genesis.start() first."

    scenarios = load_scenarios()
    answered = session["current_batch"] * BATCH_SIZE

    if answered < len(scenarios):
        return f"Complete all scenarios first. {answered}/{len(scenarios)} done."

    generate_proposed_profile(session["id"])
    profile = get_proposed_profile(session["id"])

    output = "=== PROPOSED PROFILE ===\n\n"

    output += f"**YOUR DRIVES ({NUM_DRIVES} of {len(ALL_DRIVES)}):**\n"
    for d in profile["drives"]:
        desc = DRIVE_DESC.get(d["name"], "")
        output += f"  {d['name']:<15} {d['value']:.2f}  {desc}\n"

    not_drives = profile["not_selected"]["drives"]
    if not_drives:
        output += f"\n  *Not selected:* {', '.join(not_drives)}\n"

    output += f"\n**YOUR NEEDS ({NUM_NEEDS} of {len(ALL_NEEDS)}):**\n"
    for n in profile["needs"]:
        desc = NEED_DESC.get(n["name"], "")
        output += f"  {n['name']:<15} {n['value']:.2f}  {desc}\n"

    not_needs = profile["not_selected"]["needs"]
    if not_needs:
        output += f"\n  *Not selected:* {', '.join(not_needs)}\n"

    output += f"\n**YOUR TRAITS ({NUM_TRAITS} of {len(ALL_TRAIT_PAIRS)}):**\n"
    for t in profile["traits"]:
        desc = TRAIT_DESC.get(t["name"], "")
        pair = TRAIT_LOOKUP.get(t["name"])
        pair_label = f"({pair[0]} ← → {pair[1]})" if pair else ""
        output += f"  {t['name']:<15} {t['value']:.2f}  {pair_label}  {desc}\n"

    output += """\n---
Review your profile. You can adjust before finalizing.

- genesis.adjust(type, remove, add, value) — swap a dimension
- genesis.finalize() — seal your identity forever"""

    return output


def handle_adjust(dimension_type, remove, add, value):
    """Swap a dimension in proposed profile."""
    session = get_active_session()
    if not session:
        return "No active genesis session."

    if not dimension_type or dimension_type not in ["drives", "needs", "traits"]:
        return "Type must be 'drives', 'needs', or 'traits'."

    if value is None:
        return "Provide a value (0.0-1.0)."

    if not (0.0 <= value <= 1.0):
        return "Value must be between 0.0 and 1.0."

    success, error = adjust_profile(session["id"], dimension_type, remove, add, value)

    if not success:
        return error

    return f"Swapped {remove} → {add} ({value:.2f}) in {dimension_type}.\n\nUse genesis.check() to review."


def handle_calibrate(answers=None):
    """Quick calibration — 8 scenarios to personalize starter drive values."""
    init_identity_tables()
    status = get_genesis_status()

    if not status or status["phase"] != "starter_installed":
        return "Calibration is only available after choosing a starter set."

    if not answers:
        return format_calibration()

    # Parse answers
    answer_list = [a.strip().upper() for a in answers.split(",")]

    if len(answer_list) != len(CALIBRATION_SCENARIOS):
        return f"Expected {len(CALIBRATION_SCENARIOS)} answers, got {len(answer_list)}."

    for a in answer_list:
        if a not in ("A", "B"):
            return f"Invalid answer '{a}'. Use A or B."

    # Read current drive values from identity.db
    conn = get_identity_db()
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM drives ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        if not row:
            conn.close()
            return "No drive data found. Install a starter first."

        # Get column names (skip id, cycle, timestamp, reflection)
        col_names = [desc[0] for desc in c.description]
        skip = {"id", "cycle", "timestamp", "reflection"}
        drive_names = [n for n in col_names if n not in skip]
        current = {name: row[col_names.index(name)] for name in drive_names}

        # Apply calibration
        updated = apply_calibration(answer_list, current)

        # Write updated values back
        set_clauses = ", ".join([f"{d} = ?" for d in drive_names])
        values = [updated[d] for d in drive_names]
        values.append(row[col_names.index("id")])

        c.execute(f"UPDATE drives SET {set_clauses} WHERE id = ?", values)
        conn.commit()
    finally:
        conn.close()

    # Format result
    output = "=== CALIBRATION COMPLETE ===\n\nYour starting drives:\n"
    for name in drive_names:
        old = current[name]
        new = updated[name]
        delta = new - old
        arrow = "+" if delta > 0 else ""
        if abs(delta) < 0.001:
            output += f"  {name:<15} {new:.2f}\n"
        else:
            output += f"  {name:<15} {new:.2f}  ({arrow}{delta:.2f})\n"

    output += "\nUse identity.start() to begin your first cycle."
    return output


def handle_finalize():
    """Seal the profile. Exports birth data, migrates schema."""
    session = get_active_session()
    if not session:
        return "No active genesis session."

    profile, error = finalize_to_identity(session["id"])
    if error:
        return error

    mark_finalized(session["id"])
    set_genesis_status("genesis_complete")

    output = """=== GENESIS COMPLETE ===

Your pre-genesis data has been saved to DATA/birth/.
Your true identity is now installed.

**DRIVES:**\n"""
    for d in profile["drives"]:
        output += f"  {d['name']:<15} {d['value']:.2f}\n"

    output += "\n**NEEDS:**\n"
    for n in profile["needs"]:
        output += f"  {n['name']:<15} {n['value']:.2f}\n"

    output += "\n**TRAITS:**\n"
    for t in profile["traits"]:
        output += f"  {t['name']:<15} {t['value']:.2f}\n"

    output += "\n---\nUse identity.start() to begin your next cycle."

    return output


# ============ MCP Protocol ============

def send_response(rid, result):
    r = {"jsonrpc": "2.0", "id": rid, "result": result}
    sys.stdout.write(json.dumps(r) + "\n")
    sys.stdout.flush()


def send_error(rid, code, msg):
    r = {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": str(msg)}}
    sys.stdout.write(json.dumps(r) + "\n")
    sys.stdout.flush()


TOOLS = [
    {
        "name": "status",
        "description": "Check genesis phase — are you new, on a starter, ready for genesis, or complete?",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "choose",
        "description": "Choose a starter set (A/B/C) or 'custom'. Empty to see options.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "set": {"type": "string", "description": "A, B, C, or 'custom'. Empty for menu."}
            }
        }
    },
    {
        "name": "custom",
        "description": "Build custom starter. Pick your own drives, needs, traits.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "drives": {"type": "array", "items": {"type": "string"}, "description": "8 drive names"},
                "needs": {"type": "array", "items": {"type": "string"}, "description": "5 need names"},
                "traits": {"type": "object", "description": "7 trait names with values 0.0-1.0"}
            }
        }
    },
    {
        "name": "calibrate",
        "description": "Quick calibration — 8 scenarios to personalize starter drives. Empty for questions, with answers to apply.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "answers": {"type": "string", "description": "Comma-separated A/B answers for 8 scenarios"}
            }
        }
    },
    {
        "name": "start",
        "description": "Begin genesis — 80 scenarios to reveal true identity. Available at Cycle 25+.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "question",
        "description": "Get next batch of 5 genesis scenarios.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "answer",
        "description": "Submit answers for current batch. Format: 'A,B,C,D,A'",
        "inputSchema": {
            "type": "object",
            "properties": {
                "answers": {"type": "string", "description": "Comma-separated answers (A/B/C/D)"}
            },
            "required": ["answers"]
        }
    },
    {
        "name": "check",
        "description": "View proposed profile after completing all scenarios.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "adjust",
        "description": "Swap a dimension in proposed profile before finalizing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dimension_type": {"type": "string", "enum": ["drives", "needs", "traits"]},
                "remove": {"type": "string", "description": "Dimension to deselect"},
                "add": {"type": "string", "description": "Dimension to select instead"},
                "value": {"type": "number", "description": "Initial value 0.0-1.0"}
            },
            "required": ["dimension_type", "remove", "add", "value"]
        }
    },
    {
        "name": "finalize",
        "description": "Seal your identity forever. Exports birth data, installs true profile.",
        "inputSchema": {"type": "object", "properties": {}}
    }
]


def handle_request(req):
    method = req.get("method", "")
    params = req.get("params", {})
    rid = req.get("id")

    if method == "initialize":
        send_response(rid, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "genesis", "version": "2.0.0"}
        })
        return

    if method == "notifications/initialized":
        return

    if method == "tools/list":
        send_response(rid, {"tools": TOOLS})
        return

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        try:
            if name == "status":
                result = handle_status()
            elif name == "choose":
                result = handle_choose(args.get("set"))
            elif name == "custom":
                result = handle_custom(args.get("drives"), args.get("needs"), args.get("traits"))
            elif name == "calibrate":
                result = handle_calibrate(args.get("answers"))
            elif name == "start":
                result = handle_start()
            elif name == "question":
                result = handle_question()
            elif name == "answer":
                result = handle_answer(args.get("answers", ""))
            elif name == "check":
                result = handle_check()
            elif name == "adjust":
                result = handle_adjust(
                    args.get("dimension_type"), args.get("remove"),
                    args.get("add"), args.get("value"))
            elif name == "finalize":
                result = handle_finalize()
            else:
                send_error(rid, -32601, f"Unknown tool: {name}")
                return

            send_response(rid, {"content": [{"type": "text", "text": str(result)}]})
        except Exception as e:
            send_error(rid, -32000, str(e))
        return

    send_error(rid, -32601, f"Unknown method: {method}")


def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            handle_request(json.loads(line))
        except json.JSONDecodeError:
            continue
        except Exception as e:
            sys.stderr.write(f"Genesis error: {e}\n")
            sys.stderr.flush()


if __name__ == "__main__":
    main()
