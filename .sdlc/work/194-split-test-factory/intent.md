---
id: 194
slug: split-test-factory
tier: 1
impact: none
stage: shipped
created: 2026-11-20
opened: 2026-11-19T23:50Z
updated: 2026-11-20
shipped: 2026-11-20
idea:
depends_on:
serves: none
---

# 194 — Split tests/test_factory.py along the factory's modules

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`tests/test_factory.py` has grown to 6,212 lines and 279 tests: it was 5,712 when
docs/RETRO-SCORECARD.md named it as refactor R5, after +4,773 lines in one window. It holds the
tests for all three of the factory's modules (`factory.py`, `landing.py` and `run_state.py`) in
one file. So finding the tests for a function means searching the whole file, every factory
change edits it (a train's resolver sees conflicts there most often), and a builder reads far more
of it than its change touches. Nit 2026-11-19-37: R1's `land` field is never asserted on a row
that `cmd_agent` writes for a landing task.

## Outcome

- The factory's tests live in files that follow its modules: one per module, or per area within
  `factory.py` where a single file would still be large. No file is past about 2,000 lines.
- Every test that ran before still runs, with the same name, and is still marked `portable` where
  it was. The count of tests the gate collects is unchanged, apart from the new assertion for
  nit -37.
- Shared fixtures and helpers live in one place both files import, not copied.
- The nit is fixed.

## Affected

- `tests/test_factory.py`, split into new `tests/test_factory_*.py` files.
- `tests/conftest.py`, or a shared helper module.
- Any test that imports a helper from `test_factory.py` by name.
- **What reads it:** the gate (`./check.sh`, `pytest -n auto`), CI's Windows job (`-m portable`),
  and the factory's reviewers. Nothing a host reads.

## Constraints

- No test is weakened, renamed or dropped in the move. It's a move, not a rewrite.
- `pytest -n auto` still distributes cleanly, with no fixture that depends on file order.
- `tests/test_windows.py`'s rules and `test_nothing_local` still hold in the new files.

## Approach

Group the tests by the module and function they exercise: `landing.py`'s train, land and eject
tests; `run_state.py`'s; and `factory.py`'s agent, gate, verdicts, decisions and records tests.
Move them in place, then pull the helpers they share into a shared module. Check that the gate
collects the same test ids before and after, except for the new one.

Nits taken in: 2026-11-19-37

## Open questions

- One file per module, or split `factory.py`'s tests further by area (agent, gate, verdicts,
  decisions)?
- Should it land before 191-tests-paydown and 193-ledger-and-landing-fixes, which also touch the
  factory's tests?
