---
id: 088
slug: board-progress
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: 2026-11-17-15
depends_on:
serves: [O6]
---

# 088 — The board shows how far each change has got

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The board (`/sdlc:dashboard`) shows a factory change's column, its rounds so far (`c.rounds` in
`scripts/board.html`), its assumed defaults and its cost. It doesn't show which step is running
now, how long that step has been going, or how much is left. A run spends hours in its build
column (builder, gate, the reviewers in parallel, verifier, rework, approver, each a headless
session in the background), and nothing on the card tells the person whether it's on its first
review round or nearly at the approver. The only way to find out is to ask (`factory.py verdicts`,
or the supervisor session), which is exactly what the board is supposed to make unnecessary.

The data mostly exists already. `loop_state()` (`plugins/factory/scripts/factory.py:1014`) reads
the rounds, the gate records, the verifier's `verified.md`, the decision and the ledger.
`runs/costs.jsonl` holds each agent session's `duration_ms` by role. Each `Close` commit's
`Sdlc-Stage … elapsed=` lines give a closed change's time per stage. None of this reaches the card
as progress.

## Outcome

- **Moves O6:** the person can see from the board how far each factory run has got and roughly how
  long its current step has left, and so needs to check on a run only when its card says it's
  waiting on them.
- A factory card shows a step track: build, gate, reviews *n/m*, verify, rework, approve. Done,
  current and remaining steps are visibly different, and the track is derived on each refresh from
  the files the run left in the change's folder.
- The current step shows a bar of its elapsed time against the typical time for that step and tier,
  from history. It is labelled an estimate and never passes about 95% until the step ends. With no
  history for that step and tier, it shows elapsed time alone.
- Under the bar, a hint of how many of `plan.md`'s named files the branch has touched so far.
- Nothing is stored: the board still writes nothing. `tests/test_board.py` pins the step reading
  against `factory.py`'s, as it already pins the other copies.
- `./check.sh` passes.

## Affected

- **Area:** the board, reading what factory runs and closed changes left behind.
- **Files & components:** `scripts/board.py` (`_factory()`, `state()`), `scripts/board.html` (the
  factory card), `tests/test_board.py`, and AGENTS.md's *The board* plus `docs/REFERENCE.md` if
  they list what a card shows.
- **Downstream:** the person looking at the board. Nothing else reads `/state.json`.
  `scripts/board.py` and `board.html` are `[ui]` paths, so a factory run on this change gets the ui
  and ux reviewers.
- **Contracts:** AGENTS.md's *The board*: it writes nothing, starts nothing, never imports or runs
  `factory.py`, reads the factory's files with copies of its parsing pinned by tests, and builds
  every node with `textContent`.
- **Related:** 086-board-signals-by-stage (open) also edits `board.py`'s factory reading and
  `test_board.py`, so whichever lands second rebases onto the other. This change doesn't wait on
  it.

## Constraints

- The board writes nothing, starts nothing and never imports or runs `factory.py`. It reads with
  copies of the factory's parsing, each pinned by a test.
- Each card builds its nodes with `textContent`.
- An estimate never reads as a promise: it is labelled, capped below 100% while the step runs, and
  absent rather than invented when history has none.
- A refresh stays cheap. Any read of history (`Close` trailers, closed changes' `costs.jsonl`) must
  not walk the whole log on every request.
- A change built by hand isn't given a factory step track. Whether it gets anything is an open
  question.

## Open questions

- ~~How does the board tell that a step is running, and since when? `costs.jsonl` gets a row only
  when a session ends, and `runs/<agent>.sessions` holds ids, not start times. Does it need a start
  time the factory already writes somewhere, or a new one?~~ Resolved: a new one. `verdicts
  --record` writes `runs/step.md` (step, round, limit, reviewers, since), which the loop never
  reads (spec R1–R3); the first build falls back to `runs/builder.sessions`' time (R6).
- ~~Where does "typical time for that step and tier" come from? A closed change's folder is gone from
  `main`, so its `costs.jsonl` is only in history, and `Sdlc-Stage`'s `elapsed` is per stage, not
  per factory step. Should it be per role from history, cached in memory by the board, or something
  `measure` adds to the `Close` commit?~~ Resolved: from each closed change's own `costs.jsonl` and
  gate records at `Close^`, split into steps by role and order, cached in memory per base-branch
  tip (R9–R10).
- ~~How many past runs make a usable typical time, and median or something else?~~ Resolved: the
  median of the newest 20 closed factory changes, shown only with 3 or more of the tier (R8–R9).
- ~~Does the step track come from a copy of `loop_state()`'s step logic, pinned by a test, or does the
  board stop at what the files show directly (round folders, gate records, `verified.md`,
  `decision.md`)?~~ Resolved: neither; the board reads the step `loop_state()` named, through
  `runs/step.md`, with regexes pinned to `factory.py`'s (R4, R7).
- ~~Does a change built by hand get a progress hint too (its stage, `plan.md`'s files touched), or
  does progress stay factory-only?~~ Resolved: factory-only (R11, R14).
- ~~Is the `plan.md` hint worth having when a plan names files loosely, or only with a Tier 2 plan's
  file list?~~ Resolved: only where `plan.md`'s `## Files to change` yields a path-like entry, with
  a `TEMPLATE_READS` entry for that heading (R11–R12).
