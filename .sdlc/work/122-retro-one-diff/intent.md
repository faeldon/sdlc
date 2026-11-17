---
id: 122
slug: retro-one-diff
tier: 1
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-18
shipped: 2026-11-18
idea: 2026-11-17-88
depends_on:
serves: [O5]
---

# 122 — Retro reads each change's diff once

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

**2026-11-17-88:** `retro()` and `retro_report()` each call `_change_rows()` per change, and 118's
`_spend()` now adds one `git diff -U0` per change on top, while `_rework()` already runs the same
`-U0` diff for the same change. So a retrospective runs that diff twice per change, and a host
with a long window waits on twice the git calls it needs.

## Outcome

- One `git diff -U0` per change in a retrospective, shared by `_rework()` and `_spend()`.
- `retro`'s output is byte for byte what it is today.
- A test counts the git calls `retro()` makes on a fixture window and fails if the `-U0` diff runs
  more than once per change.
- **Moves O5:** a retrospective costs a host fewer git calls.

## Affected

- **Area:** the retrospective.
- **Files & components:** `scripts/retro.py` (`_rework()`, `_spend()`, `_change_diff()`),
  `tests/test_retro.py`.
- **Downstream:** `/sdlc:retro` in every host.
- **Contracts:** `retro` is read-only but for its report; `indicators.py` stays pure.

## Constraints

- No change to what `retro` reports, or to the order it reports it in.

## Approach

Read each change's `-U0` diff once in `retro()`, keyed by the change, and hand it to both
`_rework()` and `_spend()`. Pin the call count with a test that wraps `sdlc._git`.

## Open questions

- None.
