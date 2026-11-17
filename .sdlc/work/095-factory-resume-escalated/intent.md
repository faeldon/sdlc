---
id: 095
slug: factory-resume-escalated
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: 2026-11-17-16
depends_on: [086]
serves: [O6]
---

# 095 — An escalated factory run can be sent back for another build

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

When the factory's approver says ESCALATE, the change ends at `stage: test` with `decision.md`
opening `DECISION: ESCALATE`, and the only ways on are `/sdlc:ship` by hand (taking the
escalation's reasons as the person's own work) or `/sdlc:drop`. The factory can't take it again:
`factory.py start` refuses a change at `stage: test` (`STARTS` in
`plugins/factory/scripts/factory.py` has no `test` for either tier), and even moved back to
`build` by hand, `verdicts` reads the old `decision.md` (`read_decision()`) as the run's end and
says `done` at once. So the approver's reasons, the part of an escalation that says what to do
next, reach no builder. On 2026-11-17 this came up while building 085 (stopped runs on the board),
and it is why 086's stage-gated board columns matter here: a change sent back must leave Ready and
Needs-you for Build, by its stage, not by its old decision.

## Outcome

- **Moves O6:** an escalated factory change can be handed back to the factory with its
  escalation's reasons, rather than finished by hand or dropped, so the person's stop at an
  ESCALATE is a decision about direction, not the start of manual work.
- `factory.py start NNN --for build` accepts a change at `stage: test` whose `decision.md` is an
  ESCALATE, and refuses one whose decision is READY or missing, or that isn't at `test`; tests pin
  each.
- Starting it keeps the old decision as `decision-<n>.md` (n counting from 1, never overwritten),
  moves the change to `stage: build`, and `verdicts` no longer reads `done` from the old decision;
  a test runs start then `verdicts` and gets a builder step.
- The next builder step is told the escalation's reasons (its `decision-<n>.md`, the
  `## Reconsider the approach` section where there is one), and its report lands in a new round,
  reviewed like any; a test reads the composed prompt.
- The round limit and the gate's fixes count from the restart, or the spec says why not; the board
  and status show the resumed change in Build (with 086's stage-gating) and still read the old
  decision as history, not as the run's; `land` and ship read only the current `decision.md`.
- `./check.sh` passes.

## Affected

- **Area:** the factory's start and loop, and the files a run leaves.
- **Files & components:** `plugins/factory/scripts/factory.py` (`STARTS`, `cmd_start()`,
  `read_decision()` callers, `loop_state()`, the builder's prompt), `plugins/factory/skills/build/SKILL.md`
  (what start accepts, the restart's report), `scripts/board.py` (its pinned copies, if it reads
  `decision-<n>.md`), `tests/test_factory.py`, `tests/test_board.py`, AGENTS.md's factory
  paragraph, `docs/REFERENCE.md`.
- **Downstream:** the supervisor (`/sdlc-factory:build`), `/sdlc:ship` (reads rounds and the
  decision), `/sdlc-factory:land` (`land-check`'s ESCALATE signal), the board and status, close's
  `measure` (`_factory_files()`'s counts across the restart). Waits on 086, whose stage-gating the
  board needs to show a resumed change in the right column.

## Constraints

- No agent commits; the restart writes only the change's own uncommitted folder, and `HEAD` still
  stops a run if it moves.
- An old decision is never deleted or rewritten: it stays readable as history.
- A READY change is never restarted by this path; it's ship's.
- The board's and status's copies of the factory's parsing stay pinned by tests.
- `verdicts` still decides from the rounds alone and never reads a state file.

## Open questions

- ~~Does the restart reset the round limit, or does the old run's rounds count against it (and so
  could it ever escalate again with `exhausted`)?~~ Resolved: it counts from the restart, through
  the restart record; a restarted run can exhaust and escalate again (spec R7).
- ~~Where do the escalation's reasons reach the builder: through `verified.md`-like KEPT lines, the
  decision file as is, or a new prompt section?~~ Resolved: a new prompt from `_task("build")`
  naming `decision-<n>.md` and quoting its Reconsider section (R6).
- ~~Is a run's history numbered (`decision-1.md`, `reviews/round-4/`…) or does a restart open a
  `runs/attempt-2/`-style subfolder?~~ Resolved: numbered, `decision-<n>.md` from 1, rounds
  carrying on, plus `build/round-<R>.restart.md` (R3).
- ~~Should `start` ask for the person's own words on what to change, recorded in `decisions.md` as
  build's `revise` is, or only carry the approver's reasons?~~ Resolved: optionally, a typed
  `yes, <words>` becomes an `R<k> (person, restart)` line passed by id (R6, R12).
- ~~Does an escalation after `exhausted` (reconsider the approach) restart at the spec for a Tier 2,
  or always at the build?~~ Resolved: always at the build (R1, Alternatives).
