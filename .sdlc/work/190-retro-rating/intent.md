---
id: 190
slug: retro-rating
tier: 2
impact: minor
stage: shipped
created: 2026-11-20
opened: 2026-11-19T23:48Z
updated: 2026-11-20
shipped: 2026-11-20
idea: 2026-11-20-6
depends_on: [189]
serves: [O4]
---

# 190 — The retrospective asks how working with the process felt

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The scorecard measures the process from its records, but never asks the person who lives in it.
S16 (2026-11-20-6): "The person's experience — one rating and one line asked at the
retrospective's approval, recorded in its report. A change to a WAIT, so Tier 2." Nit
2026-11-19-18: nothing checks that `REFERENCE.md` and the retro skill's Step 0 name the keys 168
added.

## Outcome

- The retro skill's WAIT asks for one rating and one line, and the committed report records both.
- The next retrospective reads the last rating back as a trend.
- A test pins the docs keys.
- **Moves O4:** the direction weighs how the work felt, not only what it counted.

## Affected

- `skills/retro/SKILL.md` (its WAIT), `scripts/retro.py`, `templates/retro.md`,
  `docs/REFERENCE.md`, `tests/test_retro.py`, `tests/test_skills.py`.
- It builds on retro-insights' report layout.

## Constraints

- Exactly one WAIT heading, asked in a dialog. A dismissed rating is no rating, never a default.
- `retro-commit` still writes only its four files.

## Open questions

- ~~Which rating scale?~~ Resolved: 1 to 4, smooth / fine / rough / in the way (spec R1, R4).
- ~~Is the rating part of the approval's answer, or a dialog of its own before it?~~ Resolved: a
  second question in the approval's own dialog, asked after it (spec R1).
