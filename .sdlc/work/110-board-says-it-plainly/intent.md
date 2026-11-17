---
id: 110
slug: board-says-it-plainly
tier: 1
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: [2026-11-17-52, 2026-11-17-56, 2026-11-17-57, 2026-11-17-58, 2026-11-17-69, 2026-11-17-70]
depends_on:
serves: [O6]
---

# 110 — The board says what it means, plainly

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The board's cards and columns still say a few things unclearly or not at all, each one left undone by
098 or 107 when they landed:

- **2026-11-17-52:** in `scripts/board.html`, the `.col-head` row lets the "who" subtitle wrap beside
  the heading, so the Test column's "the gate and the review" sits indented under a one-line title
  and looks misaligned at 1280px.
- **2026-11-17-56:** an empty column (Design, Test, Ready to ship, Ready to close in 098's
  screenshots) shows a bare "—", which doesn't say the column is empty or that nothing waits there.
- **2026-11-17-57:** a card at `build` with both a problem and a pending decision names only "fix
  what its problems name" as its next step, so it no longer says a decision is waiting too.
- **2026-11-17-58:** the rebasing card's `--abort` wording doesn't say that `resolve --abort` keeps
  the resolved work under `refs/sdlc/end/<branch>`.
- **2026-11-17-69:** a stop record that won't read shows differently in the two places. The board
  makes it a problem (`fix: runs/stopped.md doesn't open …`, card `stopped: None`, as 086 pinned),
  while `status`'s `factory_stop()` keeps it a stop (`stopped: read runs/stopped.md`).
- **2026-11-17-70:** `next_action()` ignores what 107's `needs you:` line says. An escalation that
  still needs `decide D2` names `/sdlc:ship, or /sdlc-factory:land …` as its next step.

## Outcome

- Each column's subtitle sits under its heading at 1280px and at phone width.
- An empty column says in words that nothing is waiting there.
- A card with a problem and a pending decision names both in its next step.
- The rebasing card says that `--abort` keeps the resolved work under `refs/sdlc/end/<branch>`.
- An unreadable `runs/stopped.md` reads the same way on the board and in `/sdlc:status`.
- A card's next step follows its `needs you:` line: a change that still needs `decide D2` names
  that first.
- Tests in `tests/test_board.py` (and `tests/test_sdlc.py` for `status`) pin each.
- **Moves O6:** the person reads what each change needs from one card, without asking the
  supervisor.

## Affected

- **Area:** the board and `status`.
- **Files & components:** `scripts/board.html` (`.col-head`, the empty column), `scripts/board.py`
  (`next_action()`, the stop record), `scripts/sdlc.py` (`factory_stop()`, if the two meet on its
  side), `tests/test_board.py`, `tests/test_sdlc.py`.
- **Downstream:** whoever watches the dashboard or reads `/sdlc:status`; the factory's ui and ux
  reviewers.
- **Contracts:** the board writes nothing, serves `127.0.0.1` alone and builds every node with
  `textContent`; its copies of `factory.py`'s parsing stay pinned.

## Constraints

- Aligning the stop record changes one of two pinned behaviours (086's or `status`'s); the test
  that pins the other one moves with it, never silently.
- No new dependency for the page.

## Approach

Fix the `.col-head` row with CSS alone (heading and subtitle stacked) and give an empty column a
line of text in place of the "—". Make `next_action()` read the `needs` it already computes for
107's line: a pending decision first, then problems, then the ship or land step. Name both when a
change has a problem and a decision. Align the stop record on `status`'s reading (a stop whose
record won't read, with "read runs/stopped.md") and update 086's pinned test, since a stop is what
the person sees in both places. Add the `refs/sdlc/end/<branch>` clause to the rebasing card.

## Open questions

- Should an unreadable stop record read as a stop (`status`'s way) or as a problem (the board's)?
  The Approach takes `status`'s way.
