---
id: 120
slug: board-nits
tier: 1
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-18
shipped: 2026-11-18
idea: [2026-11-17-81, 2026-11-17-82, 2026-11-17-83, 2026-11-17-84]
depends_on:
serves: [O6]
---

# 120 — The board's cards wrap, and say a stop plainly

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

110-board-says-it-plainly landed with four small things its reviewers found and left, each
carried forward as a seed:

- **2026-11-17-81:** in `scripts/board.html:82`, `.next code` has no `overflow-wrap`, so a long
  unbroken token in a card's next step could push past a narrow card.
- **2026-11-17-82:** a stopped run's `next:` line is a long run-on command in monospace (for
  example "rerun /sdlc-factory:build 006, whose one mend asks again…"), and it wraps badly at
  390px. The text comes from the factory's stop record, the `NEXT:` line `factory.py` writes from
  `WAYS`.
- **2026-11-17-83:** `scripts/board.py:393` reads
  `if entry.get("stopped") or (folder / STOPPED).is_file() and entry["stage"] == "build":`, which
  mixes `or` and `and` with no parentheses. The `and` binds first, so it works, but it's easy to
  misread.
- **2026-11-17-84:** a stop waiting on the person reads `needs you: stopped: mend` (`sdlc.py`
  around line 4108). `mend` is the factory's word for asking an agent again, not one a person
  knows. The card's `next:` line spells the step out, but the label isn't plain.

## Outcome

- A long token in a card's next step wraps inside the card at 390px and at 1280px.
- A stopped run's next step reads in a line or two at phone width.
- `_progress()`'s stop test is parenthesised, and reads the same as today.
- The needs-you line for a stop says in plain words what it waits on, for example
  `needs you: stopped, an agent asked again`, never the bare word `mend`.
- Tests in `tests/test_board.py` and `tests/test_sdlc.py` pin the wrap rule, the needs-you
  wording and the stop test's result.
- **Moves O6:** the person reads what a stopped change needs from its card, on any screen.

## Affected

- **Area:** the board and `status`.
- **Files & components:** `scripts/board.html` (`.next code`), `scripts/board.py`
  (`_progress()`), `scripts/sdlc.py` (the needs-you wording), possibly
  `plugins/factory/scripts/factory.py` (`WAYS`, the stop's `NEXT:` text), tests.
- **Downstream:** whoever watches the dashboard or reads `/sdlc:status`; the ui and ux reviewers.
- **Contracts:** the board writes nothing and builds every node with `textContent`; its copies of
  `factory.py`'s parsing stay pinned (`NEXT_RE`); a `WAYS` wording change keeps the record's
  shape.

## Constraints

- If the stop's `NEXT:` wording changes in `factory.py`, the board's pinned copy changes with it.
- No new dependency for the page.

## Approach

Add `overflow-wrap: anywhere` to `.next code`. Shorten each `WAYS` sentence in `factory.py` to the
command and a few words, and keep the longer explanation in the stop record's body, where the
board's drawer shows it. Parenthesise the `_progress()` test with no change to its result. Give
each stop way a plain label for the needs-you line. Pin each with a test.

## Open questions

- Should the shorter stop wording change in `factory.py`'s `WAYS`, or only in how the board shows
  it? `factory.py` is also edited by 112, 113 and 119, now building.
