---
id: 107
slug: board-needs-you
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on: [098, 099]
fixes: [2026-11-17-50]
serves: [O6, O3]
---

# 107 — The board and status say what each change needs from you

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The board's **Needs you** column holds every change whose `decision.md` says ESCALATE, and keeps it
there after the person has answered everything. On 2026-11-17, 102, 099 and 106 sat there with
every decision ticked, beside changes truly waiting on the person, so the column didn't answer
"what needs me?" and the person asked the supervisor change by change. `/sdlc:status` has the same
gap.

Bug 2026-11-17-50 is on the same page: the render key holds each change's `touched_ago` in whole
seconds, so every 2-second poll rebuilds every card (`replaceChildren`). A keyboard user Tabbed onto
a card loses focus to `body` before Enter can open it, and `#board` is `aria-live="polite"`, so a
screen reader is handed the whole board again each poll.

## Outcome

In the person's words: "each card under Needs you says what it needs (decide D<n>, confirm N
defaults, approve its spec, stopped: rerun), and an escalated change with every question answered
moves to Ready to ship marked 'escalated: answered'; /sdlc:status shows the same, with a 'what
needs me' line".

- Each card in Needs you names what it needs: `decide D2`, `confirm 3 defaults`, `approve its
  spec`, `stopped: rerun`.
- An escalated change with no pending or assumed decision sits in Ready to ship, marked
  `escalated: answered`.
- `/sdlc:status` ends with a "What needs me" line listing each change and what it needs, or
  "nothing".
- A poll rebuilds the board only when what a person sees changes, so focus survives a poll, and
  `aria-live` sits on the status line alone.
- Tests pin the column a change lands in for each state, the needs text, the render key and
  `aria-live`'s place.
- **Moves O6:** the person is stopped only for what needs them, and can see which changes those are
  at a glance.
- **Moves O3:** no round trip to the supervisor to learn what waits on them.

## Affected

- **Area:** the board and `status`.
- **Files & components:** `scripts/board.py` (columns, next action), `scripts/board.html` (render
  key, `aria-live`), `scripts/sdlc.py` (`status`), `tests/test_board.py`, `tests/test_sdlc.py`,
  `docs/REFERENCE.md` where it describes the board and `status`.
- **Downstream:** whoever watches `/sdlc:dashboard` or reads `/sdlc:status`; the factory's ui and ux
  reviewers.
- **Contracts:** the board writes nothing, serves `127.0.0.1` alone and builds every node with
  `textContent`; its copies of `factory.py`'s parsing stay pinned by tests; `status`'s JSON gains
  fields and redefines none.

## Constraints

- The needs text is read from the change's files, never stamped.
- An escalated change counts as answered only from its ledger: every line ticked, none pending.
- It builds after 098 and 099 land: all three edit `board.py` and `board.html`.

## Open questions

- ~~Is "escalated: answered" a marker in Ready to ship, or a column of its own?~~ Resolved: a
  marker, a badge and `answered: true` (spec R5).
- ~~Does `status`'s "What needs me" line replace an existing line, or add to the end?~~ Resolved:
  added at the end, after `■ Problems`.
- ~~Does a change that escalated only for touching an irreversible path, with no decision ever
  raised, count as answered?~~ Resolved: no, it needs `read the escalation`; a Reconsider
  escalation never counts as answered; `approve its spec` stays (the person, at the run's
  question; spec R4, R7).
