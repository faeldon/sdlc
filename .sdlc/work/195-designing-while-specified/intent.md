---
id: 195
slug: designing-while-specified
tier: 1
impact: patch
stage: shipped
created: 2026-11-20
opened: 2026-11-20T00:00Z
updated: 2026-11-20
shipped: 2026-11-20
idea:
depends_on:
serves: [O6]
---

# 195 — The board shows a change being specified under Designing

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

In the person's words: "The board shows a change under Designing while its spec-writer drafts or
its draft waits for the person's yes, read from runs/step.md and runs/spec-draft.md, not by
stamping stage: design early."

The factory leaves a Tier 2 change at `stage: plan` while its spec-writer drafts. It moves the
change to `design` only after the person's yes, when `write-spec`, `stage design` and
`stage build` run together, so that a no leaves the change cleanly at `plan`. `column()` in
`scripts/sdlc.py` places a change by its stage (`BY_STAGE`). So for the whole draft, the board and
`/sdlc:status` show the change as Planned, as if nothing had started, while an agent is designing
it. 189-retro-insights sat that way on 2026-11-20. The records that say otherwise already exist:
the spec-writer's run writes `runs/step.md`, and its draft lands in `runs/spec-draft.md`.

## Outcome

- A factory change at `stage: plan` shows under Designing while its spec-writer runs, or while its
  draft waits for the person's yes. This holds on the board and in `/sdlc:status`, which share
  `column()`.
- Its `stage:` line is never changed to get there: a no still leaves it at `plan`, back under
  Planned once its draft is gone.
- A test fails if a `plan` change with a spec run in flight, or a waiting draft, lands in any
  column but Designing, or if one with neither leaves Planned.
- **Moves O6:** the person sees what the factory is doing, at every stage.

## Affected

- `scripts/sdlc.py` (`column()`, the entry it reads), and `scripts/board.py` if the entry needs a
  new field.
- `scripts/factory_records.py`, where core reads a factory run's files.
- `tests/test_board.py` or `tests/test_status.py`.
- **What reads it:** the board and `/sdlc:status`, for every host using the factory.

## Constraints

- Only `scripts/factory_records.py` reads a factory run's records in core, with its copies pinned
  (`tests/test_modules.py`).
- The board writes nothing, `stage:` included.
- `column()` stays the one rule the board and `status` both call.

## Approach

Have `factory_records.py` say whether a factory run's spec is in flight (`runs/step.md` names
`spec`) or a draft waits (`runs/spec-draft.md` exists and `spec.md` is still its scaffold), and put
that in the entry. In `column()`, map such a `plan` change to Designing.

## Open questions

- A draft that waits for the person's yes is a decision the person owes. Should it show under Needs
  you instead, keeping Designing for while the spec-writer runs?
