---
id: 194
slug: split-test-factory
kind: plan
created: 2026-11-20
updated: 2026-11-20
---

# 194 — Split tests/test_factory.py along the factory's modules · plan

> Written by the builder after reading `tests/test_factory.py`, for a Tier 1 change whose Approach
> touches more than a couple of files.

## What the file holds

`tests/test_factory.py` (6,212 lines, 396 collected ids, 98 of them `portable`) holds
`factory.py`'s tests only. `landing.py`'s and `run_state.py`'s own tests already live in
`tests/test_land.py` and `tests/test_train.py`; the 29 references here to `factory.landing.` and
`factory.run_state.` are factory-loop tests reading a landing helper or `loop_state()` on the way.
So the split is by area within `factory.py`, along the file's own `# ---` section banners, which
already group the tests by the function they exercise. Nothing outside the file imports from it
(only a comment in `factory.py` and a row in `docs/RETRO-SCORECARD.md` name it).

## Files to change

- `tests/test_factory.py` — removed, its tests moved whole, in their order, to:
  - `tests/test_factory_loop.py` — config, `start`, `stage`, `verdicts` and the loop, the stop
    record, "sdlc reads it like any other", verified rework and `carry`, rounds that converge,
    the step record.
  - `tests/test_factory_decisions.py` — decisions, a default's alternatives, the approver's
    weighing, `ask`, an escalated change sent back (`restart`), a run upgraded to Tier 2, and
    escalations that clear.
  - `tests/test_factory_depth.py` — depth set by risk, the builder's and behaviour check's
    evidence, the copies pinned to `sdlc`'s, and the build gate's question.
  - `tests/test_factory_agent.py` — the supervisor (models, `gate_jobs`), `agent` and its stream,
    mends, the spec draft and `write-spec`, and what each run was for.
  - `tests/test_factory_gate.py` — the gate, a build starting current (`fresh`), gates sharing the
    machine, and `check`.
  - `tests/test_factory_ui.py` — the `[ui]` table and its reviewers, shots and their ports.
  - `tests/test_factory_eval.py` — the eval, reports and scores, and the review.
- `tests/factory_helpers.py` — new: `factory` and `sdlc` loaded once by path, the scratch change
  (`_change`, `_git`, `_run`, `_review`, `_round`, …) and every other helper or constant more than
  one of the new files uses, in their original order. Imported as `from factory_helpers import …`,
  as `train_driver.py` is (pytest's rootdir puts `tests/` on `sys.path`). One module instance of
  `factory` across the files, as there was one in the single file, so a monkeypatch still reaches
  the helpers.
- `tests/conftest.py` — the `claude` fixture and its `FAKE_CLAUDE` script move here, so each file
  that asks for `claude` gets it without importing a fixture (which ruff reads as a shadowed
  import). No other test file defines a `claude` fixture.
- `plugins/factory/scripts/factory.py` — the one comment naming `tests/test_factory.py` names the
  file that now pins it.

Helpers used by one new file only stay in that file, beside its tests.

Every `# ---` section banner stays with its section's file (and the helpers file names the
sections its helpers came from); four areas that started mid-section without a banner (the `[ui]`
table, an agent's run and its figures, the shots, the shots' ports) get one, so each file reads
by its banners as the old one did.

## Work order

1. Record the collected ids, and the `portable` ones, from the old file (`/tmp`, not the tree).
2. Split mechanically by section with a throwaway script outside the tree (an `ast` pass over the
   top-level statements: tests to their section's file, shared names to `factory_helpers.py`),
   then `ruff check --fix` for unused imports and `ruff format`.
3. Collect again: the same ids, file prefix aside, and the same `portable` ids; compare every
   top-level definition's AST with the old file's. Run the new files.
4. Point the `factory.py` comment at its new file, and add the acceptance check (`checks.md`)
   that the old file is gone, no new one passes 2,000 lines, and each imports the shared module.

## Tests

No test is added or changed: every test that ran before runs with the same name and marks. The
proof is the collection compared before and after (step 3), and the new files' own run. Nit
2026-11-19-37 (a `land-review` row written by `cmd_agent` carries `land`) is already asserted, by
`tests/test_land.py::test_a_landing_records_each_step_it_takes` (added in 174's rework), so no
duplicate is written: see the report's decision.

## Rollback

`git revert` undoes all of it: only test files and a comment change, nothing is written outside
the tree.
