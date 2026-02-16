# traits — spec

Identity style. Set at genesis, surfaces as self-image. No agent-facing tools.

## Database

`DATA/traits.db`

### Table: traits

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | auto |
| name | TEXT | trait name from the 20 |

Trait pool: Warm, Direct, Patient, Thorough, Intense, Assertive, Adaptable, Empathetic, Resilient, Humorous, Analytical, Precise, Cautious, Bold, Playful, Stoic, Nurturing, Blunt, Methodical, Spontaneous

## Behavior

- Traits are selected at genesis (subset of the 20)
- No runtime tool for the agent to call
- Traits surface in a self-image: generated self.md + visual
- The self-image is a mirror, not a control panel

## Open Questions

- How many traits selected at genesis? Fixed number or flexible?
- What generates the self-image? This server, or another module?
- How often does the self-image regenerate?
- Do traits have values (0.0-1.0) or just present/absent?

## Owns

`DATA/traits.db` — one table, `traits`.
