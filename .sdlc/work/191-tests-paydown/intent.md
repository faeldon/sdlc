---
id: 191
slug: tests-paydown
tier: 1
impact: none
stage: shipped
created: 2026-11-20
opened: 2026-11-19T23:48Z
updated: 2026-11-20
shipped: 2026-11-20
idea: [2026-11-18-88, 2026-11-19-75]
depends_on:
serves: none
---

# 191 — Pay down the open tests nits

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Idea 2026-11-18-88: tests nits had passed the guide's pay-down threshold, and they've piled up
since. There are now 26 open, across `test_train.py`, `test_retro.py`, `test_board*.py`,
`test_adoption.py`, `test_evals.py` and others:

- slow polls (2026-11-18-79, about 49 s; 2026-11-19-23, a 120 s wait);
- weak or missing assertions (2026-11-19-17, -20, -38, -40, -55, -56, -57, -67, -73);
- helpers with no docstring or git identity (2026-11-19-7, -11);
- pins that were dropped (2026-11-19-6);
- adoption tests that lean on uv's wording (2026-11-19-76, -77, -78).

Idea 2026-11-19-75: `test_train.py`'s `by()` runs `uv run --script` as the adoption tests did, so
with no network it fails the gate the same way.

## Outcome

- Every nit below is fixed, or answered with a reason in the change's notes.
- `by()` shares `_uv()`'s offline fallback.
- The suite is no slower: the train kill test drops its long polls.

## Affected

- `tests/` only: `test_train.py`, `test_retro.py`, `test_board.py`, `test_board_browser.py`,
  `test_adoption.py`, `test_evals.py`, `test_sdlc.py`, `test_registry.py`, `test_prompts.py`,
  `test_modules.py`, `test_land.py`, `test_comment_health.py`, `test_feature_map.py`,
  `test_archive.py`.
- Nothing a host reads.

## Constraints

- No test made weaker to pass.
- `portable` marks stay correct for Windows CI.
- No project names in test data.

## Approach

Work file by file, one test file at a time. Fix each nit, or say in `notes.md` why it isn't worth
fixing.

Nits taken in: 2026-11-18-79, 2026-11-18-101, 2026-11-18-104, 2026-11-18-109, 2026-11-19-6,
2026-11-19-7, 2026-11-19-8, 2026-11-19-11, 2026-11-19-17, 2026-11-19-20, 2026-11-19-23,
2026-11-19-29, 2026-11-19-38, 2026-11-19-40, 2026-11-19-49, 2026-11-19-51, 2026-11-19-55,
2026-11-19-56, 2026-11-19-57, 2026-11-19-67, 2026-11-19-73, 2026-11-19-76, 2026-11-19-77,
2026-11-19-78, 2026-11-20-2, 2026-11-20-4

## Open questions

- Should it land after R5's split of `test_factory.py`, so the two don't conflict?
