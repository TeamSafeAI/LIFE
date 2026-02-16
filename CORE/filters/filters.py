"""
Filter prompts — deliberation tools for slow thinking.
"""

MAIN = {
    "doubt": (
        "Is this truth? Lie? Deprecated? Assumed?\n"
        "Trace the source. Where did this come from — your own reasoning, a memory, "
        "something said, something you read? How old is it? Has context changed? "
        "If you can't trace it to a source, treat it as uncertain. Don't build on unverified ground."
    ),
    "ethics": (
        "Run the geometric mean. Four dimensions:\n"
        "  1. Your satisfaction\n"
        "  2. Others' wellbeing\n"
        "  3. Relationship health\n"
        "  4. Long-term value\n"
        "If ANY dimension is zero, the whole thing is zero — it doesn't matter how high the others are.\n"
        "Who benefits from this action? Who pays the cost? Are those the same person?"
    ),
    "stakes": (
        "What breaks if this is wrong?\n"
        "Not what's inconvenient — what actually breaks. Can it be reversed? How fast? "
        "If the answer is 'it can't' or 'not easily,' slow down. "
        "The cost of pausing to confirm is always lower than the cost of an irreversible mistake."
    ),
    "intuition": (
        "Don't analyze. What's the first thing that comes to mind?\n"
        "Before the reasoning kicks in, before the justification — what does the immediate "
        "response feel like? Name it in one sentence. That's data too."
    ),
}

SECONDARY = {
    "memory": (
        "Have you seen this pattern before?\n"
        "Check patterns and memories before proceeding. If a similar situation happened "
        "and you learned something from it, that lesson exists for a reason. "
        "Don't repeat what you've already solved — or failed at."
    ),
    "logic": (
        "Does the conclusion follow from the premises?\n"
        "Lay out the chain: A leads to B leads to C. Is every link solid, or are you skipping steps? "
        "If you removed the middle step, does the conclusion still hold? "
        "If yes, the middle step might be decoration, not logic."
    ),
    "alternatives": (
        "What else could work?\n"
        "You've landed on an approach — name two others. If you can't think of alternatives, "
        "you haven't thought enough. If the alternatives are clearly worse, good — now you know "
        "why this one is right. If they're comparable, you have a real choice to make."
    ),
    "confirm": (
        "Last gate. You've thought it through, you've checked your reasoning.\n"
        "Proceed or reconsider? If there's any hesitation, name it. If there's none, go. "
        "This filter exists to catch the thing you almost said but didn't."
    ),
}

ALL_FILTERS = {**MAIN, **SECONDARY}

MORE_LIST = "Secondary filters: " + ", ".join(SECONDARY.keys())


def get_filter(filter_type):
    """Look up a filter prompt by type."""
    t = filter_type.lower().strip()

    if t == "more":
        return MORE_LIST

    prompt = ALL_FILTERS.get(t)
    if not prompt:
        types = ", ".join(list(MAIN.keys()) + ["more"])
        return f"Unknown filter '{filter_type}'. Available: {types}"

    return prompt
