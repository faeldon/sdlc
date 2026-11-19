---
id: 171
slug: factory-run-state
tier: 2
impact: patch
stage: shipped
created: 2026-11-19
opened: 2026-11-19T02:21Z
updated: 2026-11-19
shipped: 2026-11-19
idea: 2026-11-18-67
depends_on:
serves: none
---

# 171 — The factory's run state lives in a module of its own

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The structural debt index (scorecard R3) ranks `cmd_agent` (16 changes a window), `loop_state` and
`cmd_verdicts` (10 each) among the hottest code in `plugins/factory/scripts/factory.py`. All three
read and decide a run's state, entangled with the CLI around them, and every change to the loop
meets them and conflicts on them. 163 and 164 showed a pure move takes this down safely. The
register holds nine entries on the loop and its tests: nits 2026-11-18-68 (a redundant
`RUN_STEPS["eject"]` lookup), -69 (an orphaned agent after a SIGKILL of the loop), -80 (an
`iterdir()` that raises on a missing round folder), -84 (`_stray()`'s order in
`cmd_resolve --continue`), -70 (`train --run` stops with no test of their own), -71 (a slow
kill-test poll), -85 (a fence test mixing two cases), -98 (tests missing their `portable` marks),
and idea -67 (a Windows test for a killed train run).

## Outcome

- A module beside `factory.py`, loaded by path and bound like `landing.py`, holds the run's state
  reading: `loop_state`, `verdicts`' decisions and their helpers.
- A pure move: `verdicts`' JSON and every agent's prompt are byte-identical on the existing
  fixtures.
- The nits are fixed or answered, and the Windows kill test exists, marked `portable`.
- Nothing outside the factory changes.

## Affected

- **Area:** the factory's build loop.
- **Files & components:** `plugins/factory/scripts/factory.py`, a new module beside it,
  `tests/test_factory.py`, `tests/test_train.py`, `tests/test_modules.py`.
- **Downstream:** every factory run, here and in hosts.
- **Contracts:** `factory.py agent` stays the one place `claude` runs; `verdicts` decides from the
  rounds alone; the factory never imports `sdlc.py`.

## Constraints

- The module never imports `sdlc.py`, and is loaded by path, never imported.

## Open questions

- ~~Its boundary: whether `cmd_agent`'s task building moves too, or only state and verdicts.~~
  Resolved: only `loop_state` and the helpers only it calls; `cmd_verdicts` and `cmd_agent` stay
  (spec R1, R7).
