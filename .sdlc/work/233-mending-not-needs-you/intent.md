---
id: 233
slug: mending-not-needs-you
tier: 1
impact: patch
stage: shipped
created: 2026-11-22
opened: 2026-11-22T02:46Z
updated: 2026-11-22
shipped: 2026-11-22
idea:
depends_on:
fixes: [2026-11-22-25]
serves: [O3]
origin: self
---

# 233 — A card being mended says "mending", not "Needs you"

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

From bug 2026-11-22-25: "The board and status show a mend stop as "Needs you" while the supervisor
is already mending it: verdicts --record writes runs/stopped.md (way: mend), needs_of() turns it
into "stopped: rerun to ask an agent again", and the card stays there until the next reading after
the mend replies."

Seen on 230-nit-flow on 2026-11-22: its builder's `## Evidence` held `exit: 1 (the gate's own…)`,
`verdicts` named a `mend` stop, and the supervisor resumed the builder at once, as the build skill
says ("a stop whose `way` is `mend` is the one kind this run can mend itself"). For the whole mend
the board's card sat under Needs you, and the person couldn't tell whether to act. The landing
track already shows its own mend as a step labelled "mending" (`scripts/board.py:90`); the build
track has no such step, so a `mend` stop reaches `needs_of()` (`scripts/sdlc.py:5162`,
`FACTORY_STOP_NEEDS["mend"]`) like any other.

## Outcome

- While a build round's mend is running, the card stays in its Building column with a `mending`
  step (the role, since when), and `status` doesn't list the change under Needs you.
- `agent --task mend` records the step as it starts, so the card changes the moment the
  supervisor acts, not after the reply.
- A `mend` stop reaches Needs you only when nobody is mending it: once the role's one mend is
  used up (the way becomes `rerun`, as today), or when the stop has sat unmended past a timeout,
  saying so ("mending since 14:02: if no session is running it, rerun /sdlc-factory:build 230").
- Tests drive `needs_of()` and the board's step track through each: mend under way, mend used up,
  mend left past its timeout.
- **Moves O3:** a factory run stops its person only for what needs them, and the board says which.

## Affected

- **Area:** the board, `status`'s needs, and the factory's step record.
- **Files & components:** `scripts/sdlc.py` (`needs_of()`, `FACTORY_STOP_NEEDS`),
  `scripts/board.py` (the build track's steps and labels), `scripts/factory_records.py` (its read
  of the step and stop records, copies pinned by `tests/test_modules.py`),
  `plugins/factory/scripts/factory.py` (`agent --task mend` recording its step, `_record_step()`),
  their tests.
- **Downstream:** every host's board and `/sdlc:status`; autopilot, which mends unattended, gets
  the same reading.
- **Contracts:** `needs_of()` stays the one place the board's and `status`' needs are decided; the
  board writes nothing; `factory.py` never imports `sdlc.py`, and core reads its records through
  `factory_records.py`'s pinned copies; `runs/stopped.md` is written and removed only by a
  `verdicts --record` reading.

## Constraints

- A stop that really is the person's (`rerun`, `ship`, `parked`, a mend used up) still reaches
  Needs you at once.
- No reader guesses whether a supervisor session is alive: only files and their times decide.

## Open questions

- How long is the timeout before an unmended `mend` stop counts as the person's: a fixed figure, or
  the agent's own timeout?
- Does `agent --task mend` write the step to `runs/step.md` (as `verdicts --record` does), or does
  the board read a mend from `runs/mended` and the stop's time alone?

## Approach

In `factory.py`, `agent --task mend` writes `runs/step.md` with `STEP: mend`, its role and
`SINCE:` before it starts the session. In `sdlc.py`, `needs_of()` skips a `mend` stop while the
step record names a mend newer than the stop and younger than the timeout, and names the timeout
case otherwise; the board shows a `mend` step as "mending" on the build track, as the landing
track does. `factory_records.py`'s copies follow, pinned as now. Tests for each case above.
