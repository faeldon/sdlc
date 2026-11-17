---
id: 083
slug: board-close-card-style
tier: 1
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on:
reworks: [080]
serves: none
---

# 083 — The Ready to close column's cards render as cards

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

On `/sdlc:dashboard`, the 081 card in **Ready to close** doesn't look like a card: it has no
border, no panel background, no padding, and its title is set at 20px. `card()` in
`scripts/board.html` gives each card its column's key as a class (`card ${c.column}`), and the
Ready to close column's key is `close`. The drawer's × button uses that same class. The `.close`
rule (`scripts/board.html:95`) sets `background: none; border: 0; padding: 2px 6px; font-size:
20px`, comes after `.card` in the stylesheet and has the same specificity, so it wins. This breaks
every card in that column, not only 081. 080 caused it: it added the `close` column, and nothing
checked whether a column's key clashes with a class the page already uses.

## Outcome

- A card in Ready to close has the same border, background, padding and type size as a card in
  any other column.
- The drawer's × button looks the same as it does today.
- A test in `tests/test_board.py` fails if any key in `COLUMNS` is also a class the stylesheet
  styles outside `.col`/`.card`, so a future column can't clash the same way.

## Affected

- **Area:** the board, `/sdlc:dashboard`
- **Files & components:** `scripts/board.html` (its CSS, and the drawer button's class),
  `tests/test_board.py`
- **Downstream:** a person looking at the board. No code reads the page's class names, and the
  `column: "close"` value in `/state.json` stays the same (`tests/test_board.py:225`).
- **Contracts:** the page builds every node with `textContent` and never from a string of HTML

## Constraints

- The page still builds every node with `textContent`.
- The `column` values in `/state.json` don't change.
- The phone-width layout (`@media (max-width: 760px)`) still works.

## Open questions

- Which side gets renamed: the drawer button's class (e.g. `d-close`, matching the drawer's other
  `d-*` names) or the card's column class (a prefix such as `col-`)?

## Approach

Rename the drawer button's class to match its `d-*` siblings, so the card keeps `card close` and
`.col.close` keeps working. Add a test that reads the `COLUMNS` keys and the stylesheet's
selectors from `board.html` and fails on a clash.
