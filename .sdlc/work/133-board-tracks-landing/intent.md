---
id: 133
slug: board-tracks-landing
tier: 1
impact: minor
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on:
serves: [O6]
---

# 133 — The board tracks a change through its landing, as it does a build

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

In the person's words: "landing gates and processes are not being tracked in the dashboard when
landing from Needs You and maybe in Ready to ship as well, so there's no indication of whether a
progress is shown or the different stages in landing are being completed, similar to build."

A build shows a step track on its card (build → gate → review → verify → rework → approve), with
each step's time against the typical one, because `factory.py verdicts --record` writes
`runs/step.md` and `scripts/board.py`'s `_progress()` reads it. A landing writes nothing the board
reads: `land`, `gate --land`, `resolve`, the landing reviews, `land-verdicts` and `land --close`
keep no step record, and `_progress()` pins any change at `stage: test` with a `decision.md` to
`done`. So a change can spend many minutes landing with nothing moving on its card: 124's landing
ran two rebases, a builder's conflict resolution, two landing gates, six reviews and a verify, and
whether it was gating, reviewing, stuck or finished showed only in the supervisor's terminal.

## Outcome

- While a change is landing, its card shows a landing track: ship & commit → rebase (or resolve)
  → gate → review → verify → close, marking the current step, the landing round and the moves so
  far out of `land.moves`, and the elapsed time against the typical one where history has samples.
- A landing that stopped shows on the card with its reason, as a stopped build does, not as
  `done`.
- It shows in whichever column the card sits while landing (Ready to ship, Needs you, or Ready to
  close once committed), so a landing started from any of them is tracked.
- Tests: the landing commands write the step record on each reading; `board.py`'s copy of its
  parser is pinned, as `read_step()` is; a fixture change mid-landing renders the track.
- **Moves O6:** a person can see a landing working, or stuck, without reading the supervisor's
  terminal.

## Affected

- **Area:** the board and the factory's landing.
- **Files & components:** `plugins/factory/scripts/factory.py` (the landing commands write a step
  record, like `verdicts --record`); `scripts/board.py` (`_progress()` and a landing track);
  `scripts/board.html`; `tests/test_board.py`, `tests/test_land.py`; a fixture change under
  `tests/fixtures/board/changes`.
- **Downstream:** the person watching the board; a factory build of this adds the ui and ux
  reviewers, since it touches board paths.
- **Contracts:** the board writes nothing and serves `127.0.0.1` alone; it reads the factory's
  files with copies of its parsing, pinned by tests; every node is built with `textContent`;
  `factory.py` never imports `sdlc.py`.

## Constraints

- The build's track and its `runs/step.md` shape keep working as they do; a landing record
  extends that shape or sits beside it.
- Only `factory.py` writes the record, never a skill or the supervisor.

## Open questions

- One record (`runs/step.md`) with landing steps added, or a `runs/land-step.md` of its own?
- Which commands write it: `land-verdicts` given a `--record` like `verdicts`, or each landing
  command as it runs?
- Is there history to time landing steps against (`land-<n>.gate.md`, the review sessions), or
  does the track show elapsed time only?
- Once `land --close` succeeds the change leaves the board: does a just-landed card linger briefly
  as "landed", or just go?

## Approach

Give the landing commands a step record as `verdicts --record` writes one; teach `_progress()` to
read it for a change in its landing, with a landing `TRACK` of its own; render it on the card as
the build track is; tests for the writer, the pinned parser copy and the fixture render. No open
nits touch these paths.
