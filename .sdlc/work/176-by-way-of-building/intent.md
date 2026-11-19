---
id: 176
slug: by-way-of-building
tier: 2
impact: minor
stage: shipped
created: 2026-11-19
opened: 2026-11-19T07:57Z
updated: 2026-11-19
shipped: 2026-11-19
idea: [2026-11-19-33, 2026-11-19-13, 2026-11-19-14]
depends_on: [175]
serves: [O4, O6]
---

# 176 — The retrospective compares factory-built changes with hand-built ones

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The scorecard asks one question no figure answers yet (S9): is a factory-built change faster,
cheaper and as sound as one built by hand? Lead time, throughput, cost and escape rate are reported
for all changes together, so the Autonomy pillar's guardrail, "escape rate, factory against by
hand", can't be read. Idea 2026-11-19-33: "lead time, throughput, cost and escape rate, factory
against by hand."

Two ideas left undone by 168-work-mix-and-follow-through come in, on the same figures:

- 2026-11-19-13: "`docs/RETRO-SCORECARD.md` *Supporting: throughput* still says 'by impact S2':
  the work classes now exist, but throughput isn't broken down by them."
- 2026-11-19-14: "Follow-through's milestone `done` by grouped rows reads `_milestone_verdicts()`
  against the current register, so a grouped seed retired with `inbox-commit` reads `vanished`
  there (and the milestone `carried`), while the same seed scored as a seed reads `dropped`.
  Teaching `_milestone_verdicts()` about `Retire` subjects would change what
  `direction.milestones` reports, which the spec's boundaries say asks first." This intent is
  that asking.

And nit 2026-11-19-15: `_is_process` (`scripts/retro.py`) also skips `.sdlc/setup.json`, which
168's spec doesn't list; drop the skip or say so.

It follows pipeline-figures, the last of the three changes that add to `retro`'s factory figures.

## Outcome

- `retro`'s lead time, throughput, cost and escape rate are each given by way of building,
  factory and by hand, with each side's `n`.
- Throughput is also given by work class.
- A grouped seed retired by `inbox-commit` reads `dropped` in a milestone's verdict, as it does
  scored alone.
- The nit is fixed or answered.
- **Moves O4:** the retrospective says whether the factory's changes are worth what they cost
  against the person's own.
- **Moves O6:** an escape rate for the factory's changes beside the person's shows whether its
  autonomy can be trusted.

## Affected

- **Area:** the retrospective.
- **Files & components:** `scripts/retro.py`, `scripts/factory_records.py` if a figure needs it,
  `docs/REFERENCE.md` (*Retrospectives*), `docs/RETRO-SCORECARD.md`.
- **Downstream:** a host's retrospective; the direction doc's milestones, whose `done` verdict
  changes for a retired grouped seed.
- **Contracts:** `direction.milestones`' meaning (the change -14 asks for); `Sdlc-Mode` as the
  record of how a change was built.

## Constraints

- A change whose way of building no record says is counted as unknown, never guessed.
- A hand-built change has no dollars: its cost compares in tokens, or is reported as missing.

## Open questions

- ~~Is a change built by the factory but shipped by hand (`/sdlc:ship` from its worktree) factory
  or hand?~~ Resolved: factory, as close's `Sdlc-Mode` already records it (spec R1).
- ~~Should cost compare in dollars, with hand-built changes missing, or in tokens for both?~~
  Resolved: tokens for both, dollars where recorded (spec R6).
