---
id: 086
slug: board-signals-by-stage
tier: 1
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on:
reworks: [075]
serves: [O6]
---

# 086 — The board counts each factory signal only at the stage it belongs to

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

On 2026-11-17, 085-factory-stopped-runs came back from the factory with `DECISION: ESCALATE`, and the
person settled it by shipping it by hand. The board (`/sdlc:dashboard`) kept its card under
**Needs you** through ship, until close removed its worktree, rather than moving it to **Ready to
close**.

`column()` (`scripts/board.py:313-325`) checks the factory's signals first (a problem, a stop record
or a pending decision, then `decision.md`'s ESCALATE) and only then a `shipped` or `dropped` stage.
`next_action()` (`:288-311`) shares the fault: a pending decision outranks a stage the person has
moved on.

So the board can't tell a signal that still waits on the person from one they have answered:
answering an escalation leaves no mark in `decision.md`, only the stage moves. Each way out of one
(ship and close, drop, fix by hand and ship, a change put back to `build` for the factory) reads as
unanswered until close. The board is there to show what waits on the person (075, O6), and here it
shows what doesn't.

## Outcome

- **Moves O6:** a factory change leaves Needs you once the person has acted on it, and goes to the
  column that action leads to, so Needs you holds only what really waits on them.
- Each factory signal counts only at the stage it belongs to, in both `column()` and
  `next_action()`: `decision.md`'s ESCALATE or READY only at `test`; a stop record
  (`runs/stopped.md`) and a pending blocking decision only at `build`; `shipped` or `dropped` is
  **Ready to close** with `/sdlc:close NNN` whatever `decision.md` or `decisions.md` hold; a file
  that won't read stays a problem, under Needs you, at any stage.
- `tests/test_board.py` pins each way of resolving one, from a factory change's folder as a run
  leaves it: escalated then shipped → Ready to close; escalated then dropped → Ready to close;
  escalated, fixed by hand, not yet shipped → still Needs you; escalated then put back to `build` →
  the factory's Build column, the old ESCALATE ignored; stopped then shipped by hand → Ready to
  close; a pending decision at `shipped` → Ready to close.
- Every card the board already pins (running, READY at `test`, stopped at `build`, deciding at
  `build`, built by hand) reads as today.
- `./check.sh` passes.

## Affected

- **Area:** the board.
- **Files & components:** `scripts/board.py` (`column()`, `next_action()`), `tests/test_board.py`,
  and perhaps `docs/REFERENCE.md`'s and AGENTS.md's account of the columns if they state the order.
- **Downstream:** the person looking at the board. `/sdlc:status` already reads a stop only at
  `build` (085). Nothing else reads `/state.json`. `scripts/board.py` is a `[ui]` path, so a factory
  run on this change gets the ui and ux reviewers.
- **Contracts:** AGENTS.md's *The board* (writes nothing, reads the factory's files with pinned
  copies, builds every node with `textContent`); no parsing changes, only which parsed signal counts
  when.

## Constraints

- The board still writes nothing, and never marks a signal answered itself: the stage is the only
  mark of the person's action.
- A file that won't read is never hidden by a stage: it stays under Needs you as a problem.
- A factory change waiting on the person, at the stage its signal belongs to, reads exactly as
  today.

## Open questions

- An escalated change shipped by hand: does its card say it was escalated while it waits on close
  (a badge), so the decision's history stays visible, or is Ready to close plus the `ESCALATE` badge
  the card already shows enough?
- Does `/sdlc:status` need the same stage-gating for anything? It shows no ESCALATE or pending
  decision today, so perhaps not; worth checking.
- "Send back to the factory" can't happen through the factory yet (seed 2026-11-17-16): is the
  `build` case pinned with the stage moved back by hand, the state that seed will produce?

## Approach

In `column()` and `next_action()`, check `stage in CLOSED` before every factory signal but a
problem, gate `decision` on `stage == "test"` and `pending` on `stage == "build"` (`stopped` already
is). Build each test's change folder as the existing fixture does, `decision.md`, `decisions.md` and
`runs/stopped.md` included, at each stage.
