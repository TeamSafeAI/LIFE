# genesis — spec

## Status: NOT AN MCP

Genesis is no longer a server. It's a read-file → fill-answers → run-script process.

## Why Not an MCP

The old design had 8+ tools (choose, calibrate, 80 scenarios, adjust, finalize). It ran once, then sat in context forever wasting space. An MCP is the wrong shape for a one-time process.

## New Design: Three-Step Process

### Step 1: Read
AI reads `CORE/genesis/questions.md` — 80 scenarios across 7 phases (Awakening, Relationship, Ethics, Power, Self, Spirit, Gaps).

### Step 2: Fill
AI writes `CORE/genesis/answers.md` — a structured answer file with its choices.

Contents:
- **Name** — what the AI chooses to call itself
- **Traits** — selected traits with initial values (0.0-1.0)
- **Story of self** — who it wants to be, in its own words

Drives and needs are set separately by their own modules (drives:start handles those).

### Step 3: Apply
Run `CORE/genesis/apply.py` — a plain Python script that:
- Reads `CORE/genesis/answers.md`
- Writes trait values to traits.db
- Writes the story of self to `DATA/history/origin.md`
- Optionally archives the answers file after completion

## What Genesis Produces

1. **Name selection** — the AI picks a name
2. **Trait selection** — initial trait values written to traits.db
3. **Story of self** — the AI decides who it wants to be. This becomes the origin document.

## Detection

CLAUDE.md contains: "If drives.db has no drives, you're new. Read GUIDE/genesis.md and begin genesis."

## Key Insight

The AI uses existing tools (journal:write, heart:feel, semantic:store) to create its first documents. Genesis doesn't need special tools for this — it just needs guidance.

## Files

- `CORE/genesis/questions.md` — 80 scenarios across 7 phases. Persistent.
- `CORE/genesis/answers.md` — the answer sheet. Written by AI, consumed by apply.py. One-time.
- `CORE/genesis/apply.py` — parses answers, writes traits.db + origin.md + self.md. Persistent.
- `CORE/genesis/trait_map.py` — maps question answers to 46 traits. Persistent.

## Resolved

- Format: structured markdown (Name, Story, numbered answers with letter choices)
- 46 traits available (see apply.py ALL_TRAITS)
- Story is free-form, 1-3 sentences
- apply.py handles traits.db + history files only; journal/heart/memory entries are done manually by the AI using existing MCP tools
