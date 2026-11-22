# 230-nit-flow — entries

## [2026-11-22-29] [nit] `again` runs `_nit_path` over every later nit once for each earlier nit, so the work grows as nits × rounds × nits.

Raised by the code review of 230-nit-flow, round 1: plugins/factory/scripts/factory.py:3013: `again` runs `_nit_path` over every later nit once for each earlier nit, so the work grows as nits × rounds × nits. The sets are tiny, so computing each later round's path set once per role would be tidier than urgent.

Theme: refactor
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 230-nit-flow (correctness)

## [2026-11-22-30] [nit] the `kind != "nit" and (by or is_building(e))` branch is correct.

Raised by the code review of 230-nit-flow, round 1: scripts/sdlc.py:7776: the `kind != "nit" and (by or is_building(e))` branch is correct. A short comment would help, saying that a nit's claim check is deliberately separate from `_claimed_by`.

Theme: docs
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 230-nit-flow (correctness)

## [2026-11-22-31] [nit] the test sets `start` on a round by hand to model a restart.

Raised by the test review of 230-nit-flow, round 1: tests/test_factory_loop.py:921: the test sets `start` on a round by hand to model a restart. A restart that went through `cmd_restart` is exercised only in the R4 prompt test, not for filing.

Theme: tests
Paths: tests/test_factory_loop.py
Cost: S
Value: low
Raised by: 230-nit-flow (correctness)
