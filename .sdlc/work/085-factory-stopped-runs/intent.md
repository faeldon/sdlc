---
id: 085
slug: factory-stopped-runs
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on:
reworks: [075]
serves: [O6]
---

# 085 — A stopped factory run says so, and how to move it on

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

On 2026-11-17, 078-review-escape-classes's factory run stopped after round 1's verification (see
084): `factory.py verdicts 078` returns `next: stop` with its two problems. Nothing outside the
supervisor's own turn shows it:

- **The board** puts 078's card in **Build**, "the factory is building it: wait for its decision":
  `next_action()` (`scripts/board.py:272-273`) says that for any factory change at `design` or
  `build` with a builder report, and the board never sees a stop, since it reads the change's files
  and `verdicts` writes none.
- **`/sdlc:status`** reads `078 T1 build … touched 25m ago`, like a run in progress; once a day old
  it reads "quiet" and comes up as the one to finish, with nothing saying why it stopped or what
  would move it on.
- **Nothing says how to resume.** The person must know a stopped run can be shipped by hand, or
  picked up by `/sdlc-factory:build` again once its cause is fixed (as 078 can be after 084), and
  which fits.

A stop is exactly when the factory needs its person (O6), and today the person learns of it only
from the supervisor's message in the turn it happened.

## Outcome

- **Moves O6:** a stopped factory run says so wherever the person looks, with its reason and the
  step that moves it on, so a stop waits on them visibly rather than reading as work in progress.
- The board puts a stopped run's card under **Needs you**, its flag the stop's problems as
  `verdicts` worded them, its next step by the stop's kind: ship it by hand, rerun
  `/sdlc-factory:build NNN` once the cause is fixed, or the one mend allowed for a missing
  `## Evidence`. `tests/test_board.py` pins a stopped run built from 078's round-1 files.
- `/sdlc:status` marks a stopped run on its line, with the same reason, and never recommends it as
  merely quiet; pinned by a test.
- A run that resumes (`/sdlc-factory:build NNN` after the cause is fixed) clears the stop: the card
  goes back to its column, the status line loses its mark.
- A running factory change, one waiting on a decision, and one ready to ship read exactly as today.
- `./check.sh` passes.

## Affected

- **Area:** the factory's stop, and the two places a person reads a change's state.
- **Files & components:** `plugins/factory/scripts/factory.py` (`verdicts`' stop, perhaps a record
  of it), `plugins/factory/skills/build/SKILL.md` (the supervisor's `stop` step), `scripts/board.py`
  (`_factory()`, `next_action()`, `column()`), `scripts/sdlc.py`'s status line if status shows it,
  and `tests/test_board.py`, `tests/test_factory.py` and a status test.
- **Downstream:** the person, through the board and `/sdlc:status`; `/sdlc-factory:land` and
  `factory.py ready`, which must still leave a stopped run out; `/sdlc:ship`, which reads a factory
  change's folder; close's `measure` if a stop record is counted; hosts that run the factory.
- **Contracts:** AGENTS.md's *The factory* ("`verdicts` writes nothing", a run's state "never a state
  file"); *The board* (it writes nothing, and reads the factory's files with copies of `factory.py`'s
  parsing, pinned by tests; the core never imports or runs the factory); the factory never imports
  `sdlc.py`; the metrics trailer contract, if a stop is measured.

## Constraints

- The board and `sdlc.py` never run `factory.py`, and the board still writes nothing.
- A stop is never cleared by anything but its cause being gone: no supervisor or agent writes it
  away to get past it.
- Whatever records a stop agrees with what `verdicts` says on its next call: two accounts of one
  run's state that can disagree is the failure to avoid.
- Nothing about a running, deciding or ready run changes.

## Open questions

- ~~Where does the stop live: a file the supervisor's `stop` step writes through `factory.py` (say
  `runs/stopped.md`, the problems word for word), removed by a later `verdicts` without problems,
  which needs AGENTS.md's "verdicts writes nothing" read as "nothing about the run's state" or
  reworded; copies of `verdicts`' stop checks in `board.py` and `sdlc.py`, pinned, nothing recorded,
  three copies of logic 084 has just changed; or `factory.py verdicts --record`, run only by the
  supervisor?~~ Resolved: `factory.py verdicts --head <h> --record`, run only by the supervisor,
  writes or removes `runs/stopped.md` from the reading it prints; the loop never reads it; two
  AGENTS.md sentences reworded (spec R1-R5, Contracts touched 1 and 2).
- ~~Does `/sdlc:status` show it at all, or the board alone? Status has no factory-specific line
  today.~~ Resolved: both; status marks the line `stopped` with its problems and next step (spec R10).
- ~~Does a stop name its way on (ship by hand, rerun the build, mend) from its problem's kind, and is
  that `factory.py`'s call or the reader's?~~ Resolved: `factory.py`'s, written into the record as
  `STOPPED: ship|mend|rerun` with its sentence (spec R4).
- ~~Does 078 need anything from this change, or do 084 landing and `/sdlc-factory:build 078` resume
  it, and is that this change's live test?~~ Resolved: no; 084 landed and 078 closed without this
  change, so its round-1 files became `test_a_stopped_run_needs_the_person`'s fixture (spec R6).
