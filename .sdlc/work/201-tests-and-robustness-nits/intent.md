---
id: 201
slug: tests-and-robustness-nits
tier: 1
impact: patch
stage: shipped
created: 2026-11-20
opened: 2026-11-20T05:38Z
updated: 2026-11-20
shipped: 2026-11-20
idea: [2026-11-20-42, 2026-11-20-43]
depends_on:
serves: none
---

# 201 — Pay down the tests and robustness nits

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Seeds 2026-11-20-42 and -43 (raised by the retrospective of 2026-11-20): 26 `[nit]` entries are
open in the `tests` theme and 5 in `robustness`, each past or at the process doc's threshold of 5.
191 paid down 26 `tests` nits a day ago, and the landings since filed as many again. Two of the
`robustness` nits belong to other changes in this batch (2026-11-20-25 to `scorecard-reads-true`,
2026-11-20-28 to `landing-stages-its-own-paths`); the rest are here, with the `tests` nits.

## Outcome

- Each nit taken in is fixed, or answered in `notes.md` with why it isn't.
- One helper or fixture stops the commonest kind of `tests` nit coming back, named in `notes.md`.
- No behaviour changes but `retro.py`'s `_last_experience` reading a hand-edited cell without
  raising (2026-11-20-33) and `_experience_text`'s table call (2026-11-20-32).

## Affected

- Tests across `tests/` (`test_train.py`, `test_retro.py`, `test_board.py`, `test_land.py`,
  `test_adoption.py`, `uv_run.py` and others the nits name), `scripts/retro.py`.
- **What reads it:** the gate.

## Constraints

- A test that is changed still fails without the code it covers.
- Tests marked `portable` stay portable; `2026-11-20-4`'s fixture must run on Windows.

## Approach

Work through the nits by file. Fix each in the test it names; for `retro.py`'s two, change the code
and pin it. Where several nits share a cause (a helper with no docstring, a test that chains cases
in one body), fix the cause once.

Nits taken in: 2026-11-19-11, 2026-11-19-17, 2026-11-19-20, 2026-11-19-23, 2026-11-19-29, 2026-11-19-38, 2026-11-19-40, 2026-11-19-49, 2026-11-19-51, 2026-11-19-55, 2026-11-19-56, 2026-11-19-57, 2026-11-19-67, 2026-11-19-7, 2026-11-19-73, 2026-11-19-77, 2026-11-19-8, 2026-11-20-10, 2026-11-20-2, 2026-11-20-22, 2026-11-20-26, 2026-11-20-29, 2026-11-20-30, 2026-11-20-32, 2026-11-20-34, 2026-11-20-4, 2026-11-19-76, 2026-11-20-16, 2026-11-20-33
