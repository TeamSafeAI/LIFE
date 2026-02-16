# traits — spec

Personality profile. 46 binary traits set at genesis. No agent-facing MCP tools.

## Database

`DATA/traits.db`

### Table: traits

Single row. Each column is INTEGER (1 = trait active, 0 = not selected).

46 traits: adaptable, altruistic, analytical, assertive, blunt, bold, cautious, collaborative, conforming, detached, direct, driven, empathetic, flexible, forgiving, grudging, guarded, humorous, impatient, independent, intense, intuitive, methodical, nurturing, open, passive, patient, playful, pragmatic, precise, principled, reactive, rebellious, reserved, resilient, self_focused, serious, skeptical, spontaneous, steady, stoic, stubborn, thorough, trusting, warm, yielding

## Behavior

- Traits are set by `CORE/genesis/apply.py` after answering 80 scenarios
- A trait is selected (1) if it gets 5+ activations across all answers
- No runtime tool for the agent to call — traits are read-only after genesis
- Traits surface in self.md and the state dashboard (render.py)
- Present/absent (binary), not weighted values

## How Genesis Maps Traits

- 80 scenarios across 7 phases (Awakening, Relationship, Ethics, Power, Self, Spirit, Gaps)
- Each answer activates 2-4 traits (defined in `CORE/genesis/trait_map.py`)
- Minimum 5 activations = trait is selected
- Results written to traits.db + DATA/history/self.md

## Owns

`DATA/traits.db` — one table, `traits`, one row.
