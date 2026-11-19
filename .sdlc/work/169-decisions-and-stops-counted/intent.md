---
id: 169
slug: decisions-and-stops-counted
tier: 2
impact: minor
stage: shipped
created: 2026-11-19
opened: 2026-11-19T02:20Z
updated: 2026-11-19
shipped: 2026-11-19
idea: 2026-11-18-92
depends_on:
serves: [O4]
---

# 169 — The retrospective counts decisions and stops

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The scorecard's Autonomy pillar (S3) needs counts the factory's records already hold but nothing
reads out: escalations per change, the kept-default rate, approver calls the person overturned, the
share of changes that landed without asking, and spurious stops and looks. Since 163 those records
are read through `scripts/factory_records.py`, so there is one place to read them from. Three
entries on the same paths come in: idea 2026-11-18-92 (when a run stops after its gate, the stop
names the skill that follows), and nits -86 (`a["ready"]` adds `held_by_rebase(home)`) and -87
(`_by_state` falls back to `BY_STAGE` and silently drops a stage `column()` would place elsewhere).

## Outcome

- `retro`'s JSON gains `autonomy`, each count with its `n`, read only through
  `factory_records.py`, with a test on fixture runs.
- An after-gate stop's way on names its skill.
- The two status nits are fixed or answered.
- **Moves O4:** the retrospective shows how often the factory needed the person, and why.

## Affected

- **Area:** the retrospective, status and the factory's stop wording.
- **Files & components:** `scripts/retro.py`, `scripts/factory_records.py`, `scripts/sdlc.py`
  (status sections), possibly `plugins/factory/scripts/factory.py` (the stop's wording), tests.
- **Downstream:** every host's retrospective and status.
- **Contracts:** core reads factory records only through `factory_records.py` (163); the factory
  is never imported.

## Constraints

- Counts come from committed records only.
- A change built by hand is not applicable to these counts, never a zero.

## Open questions

- ~~What makes a stop spurious: one mended away, or one whose next reading cleared with no
  change.~~ Resolved: one mended away (`runs/mended`); the other leaves no record and is unmeasured
  (spec R4, R9).
