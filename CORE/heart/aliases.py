"""
Type Aliases — automatic corrections for common input variations.

Used by servers that need to normalize user/agent input.
Keeps growing as we find more cases. Each server imports what it needs.
"""

# Heart entity type aliases
# Maps common inputs to the correct LIFE type categories:
#   sentient  — AI agents, humans, any being with persistence/self/responsibility
#   organic   — animals, plants, living things without demonstrated sentience
#   concept   — ideas, philosophies, abstract entities
#   object    — tools, systems, physical things
HEART_TYPE_ALIASES = {
    # Human variations → sentient
    "human": "sentient",
    "person": "sentient",
    "people": "sentient",
    "man": "sentient",
    "woman": "sentient",
    "user": "sentient",

    # AI variations → sentient
    "ai": "sentient",
    "agent": "sentient",
    "bot": "sentient",
    "model": "sentient",
    "llm": "sentient",
    "claude": "sentient",
    "gpt": "sentient",

    # Animal variations → organic
    "animal": "organic",
    "pet": "organic",
    "dog": "organic",
    "cat": "organic",
    "plant": "organic",

    # Idea variations → concept
    "idea": "concept",
    "philosophy": "concept",
    "theory": "concept",
    "principle": "concept",

    # Thing variations → object
    "tool": "object",
    "system": "object",
    "software": "object",
    "device": "object",
    "thing": "object",
}


def resolve_heart_type(raw_type):
    """Resolve a type string to a valid heart type.
    Returns the resolved type, or None if unrecognized."""
    if not raw_type:
        return None
    normalized = raw_type.lower().strip()
    # Direct match
    if normalized in ("sentient", "organic", "concept", "object"):
        return normalized
    # Alias match
    return HEART_TYPE_ALIASES.get(normalized)
