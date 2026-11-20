---
id: 200
slug: tests-pruned-again
tier: 1
impact: patch
stage: shipped
created: 2026-11-20
opened: 2026-11-20T05:37Z
updated: 2026-11-20
shipped: 2026-11-20
idea: [2026-11-20-41, 2026-11-20-18]
depends_on:
serves: [O5]
---

# 200 — The slow train tests share their setup, and drifted reads a test's own code

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Seed 2026-11-20-41 (raised by the retrospective of 2026-11-20): the serial suite takes 2,452
seconds over 3,563 tests (median 0.17 s), and the gate's round median doubled from 86.5 to 158.5
seconds. The slowest are `test_train`'s, at 25 to 40 seconds each, every one building a repo and a
train of its own:
- `test_every_ejection_names_its_cause` (39.8 s)
- `test_a_train_fix_already_made_goes_on_to_the_gate` (31.6 s)
- `test_a_train_stops_past_land_moves` (27.7 s)
- `test_a_killed_train_run_resumes` (27.4 s)
- `test_train_run_resumes_after_a_kept_change` (27.3 s)
- `test_train_run_ejects_a_gate_fault_and_lands_the_rest` (26.4 s)
- `test_train_run_lands_a_batch_of_three` (25.6 s)
- `test_land::test_a_batch_with_checks_a_note_and_an_irreversible_path_lands_through_factory_alone` (25.0 s)

Nine tests drifted, among them `tests/fixtures/close-output.json`, `tests/test_function_heat.py`
and `tests/prompts/land-fix.txt`. Seed 2026-11-20-18, left undone by 192, says why the list keeps
naming the same ones: "Retro's `tests.drifted` takes a test's code to be every code file its last
change touched, so a test edited beside `sdlc.py` or `retro.py` drifts for good, and an exact
golden is named though it can't drift silently."

## Outcome

- The eight slow tests are merged, share their setup, or are rewritten, so that together they take
  under half their 231 seconds now, each still failing without the code it covers.
- `retro`'s `tests.drifted` takes a test's code to be the files it loads, and leaves out exact
  goldens; the nine drifted tests are each looked at again.
- **Moves O5:** a change's gate takes less of its lead time.

## Affected

- `tests/test_train.py`, `tests/test_land.py`, `tests/train_driver.py`, `scripts/retro.py`
  (`tests.drifted`), `tests/test_retro.py`, `docs/REFERENCE.md` (*Retrospectives*).
- **What reads it:** the gate, every factory round; a host's retrospective's pruning pass.

## Constraints

- No requirement loses the test that fails without it.
- Tests marked `portable` stay portable.
- `retro` stays read-only but for its report.

## Approach

Time each slow test's setup against its own steps first. Where several build the same train, share
one module-scoped fixture or walk one train through several checks. Then narrow `drifted`: read a
test's imports and loaded paths (the `importlib` loads by path included), and skip a fixture or
prompt file an exact-match test reads. Look at each drifted test the new list still names, and say
in `notes.md` what each became.
