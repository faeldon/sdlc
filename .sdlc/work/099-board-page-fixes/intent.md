---
id: 099
slug: board-page-fixes
tier: 1
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on:
fixes: [2026-11-17-24, 2026-11-17-25, 2026-11-17-26]
serves: [O6]
---

# 099 — The board's page works on a phone and by keyboard

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Three accessibility and layout bugs on the board's page (`scripts/board.html`), all found by the review of 086-board-signals-by-stage:

- **2026-11-17-24:** "Below 760px the columns stack in stage order, so the one that waits on the person is under all the others" (scripts/board.html:44-46).
- **2026-11-17-25:** "The drawer is `aria-modal`, but Tab moves into the page behind the scrim" (scripts/board.html:136).
- **2026-11-17-26:** "`kept 1 · dropped 2` says whose count it is only in its `title`, which keyboard, touch and screen-reader users don't get" (scripts/board.html:196-198).

## Outcome

- At phone width, Needs you comes first.
- With the file drawer open, Tab and Shift-Tab stay inside it, Escape closes it, and focus returns to what opened it.
- The verifier's chip says whose count it is in visible or accessible text (`aria-label` or a visually hidden label), not only a tooltip.
- `tests/test_board.py` pins each: the column order rule, the trap's handler, the chip's label.
- **Moves O6:** the board's column order, file drawer and verifier chip work on a phone, by keyboard and with a screen reader. A poll still rebuilds every card, dropping keyboard focus and re-reading the board to a screen reader: bug 2026-11-17-50, left for a change of its own (the person, after the approver's escalation).

## Affected

- **Area:** the board's page.
- **Files & components:** `scripts/board.html` only, and `tests/test_board.py`.
- **Downstream:** anyone watching `/sdlc:dashboard`; the factory's `ui` and `ux` reviewers when `[ui]` is set.
- **Contracts:** every node built with `textContent`, never from a string of HTML.

## Constraints

- No new dependency, framework or build step: the page stays one served file.
- Desktop layout unchanged.

## Open questions

- Visible label on the chip, or an accessible one only?

## Approach

A media-query `order` for the Needs you column below 760px; a keydown handler on the drawer that cycles focus among its focusable nodes, with Escape and focus return; an accessible name on the chip. Tests read the served page in `tests/test_board.py`.
