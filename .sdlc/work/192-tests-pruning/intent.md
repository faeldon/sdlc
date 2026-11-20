---
id: 192
slug: tests-pruning
tier: 1
impact: none
stage: shipped
created: 2026-11-20
opened: 2026-11-19T23:48Z
updated: 2026-11-20
shipped: 2026-11-20
idea: 2026-11-18-90
depends_on: [191]
serves: [O5]
---

# 192 — Prune the tests that drifted from their code

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Idea 2026-11-18-90: retro's `tests.drifted` named ten test files whose code moved without them:

- the board fixture `012-draft-publish` (seven files);
- `tests/test_config_resolution.py` and `tests/test_indicators.py`;
- `tests/test_adoption.py`.

A test that no longer tracks its code costs gate time and proves less than it claims.

## Outcome

- Each named file is looked at again and merged, rewritten, moved or deleted, with the reason in
  `notes.md`.
- `retro`'s `tests.drifted` no longer names it, unless it was kept on purpose.
- **Moves O5:** a smaller suite that still proves what it claims.

## Affected

- `tests/` and `tests/fixtures/board/012-draft-publish/`.
- The board fixture is read by the UI reviewers' screenshots.

## Constraints

- No coverage of a contract is lost: a deleted test's assertion moves, or the reason it's no
  longer needed is written down.

## Approach

Rerun `retro` for the current drifted list, then take each file in turn.

## Open questions

None.
