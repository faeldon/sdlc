---
id: 217
slug: train-gates-every-tip
kind: plan
created: 2026-11-21
updated: 2026-11-21
---

# 217 — Gate every landing train's tip, a train of one included · plan

> Written after reading `landing.py`'s train (`_train_reading()`, `_train_gate()`, `_run_end()`,
> `land_question()`, `cmd_land_check()`), `factory.py`'s `cmd_gate(..., land=True)` and the train
> tests in `tests/test_train.py` and `tests/test_land.py`.

## Files to change

- `plugins/factory/scripts/landing.py`: drop the `m == 1 and stacked == pre` return in
  `_train_gate()`; add `ungated` to `_train_reading()`'s `out` and to `_run_end()`'s summary
  (a small helper `_ungated(main, base)` shared by both, reusing `factory._base_check()`);
  `land_question(..., gated=True)`'s gate clause; `cmd_land_check()` passes `gated`; the comment
  in `cmd_land()`.
- `plugins/factory/scripts/factory.py`: the comment in `cmd_gate()`'s `land` branch.
- `plugins/factory/skills/land/SKILL.md`: Step 3's JSON keys name `ungated`; Step 4 reports it.
- `docs/REFERENCE.md`: the `gate_fail` sentence covers every change a landing gates.
- `tests/test_train.py`: the R1–R4, R6 tests.
- `tests/test_land.py`: the ungated question case (R7), `land-check` on a base with no check.
- `tests/test_skills.py`: Step 4 names `ungated` (R8).

Reused, not re-derived: `factory._base_check()` (the base branch's check), `cmd_gate`'s
`land-1` fallback for a change with no landing round, `_put_back()`/`_train_eject()` for a change
that never moved, `_gate_attempts()`/`_closes()`/`_loop()` in the tests.

## Work order

1. **The gate (R1, R2, R3, R4).** Tests first: the reading of a one-change train (both cases,
   never moved and rebased by `fresh` before `--begin`), the forbidden-file escape through
   `train --run`, the green record, the hand-written record. See them fail, then delete the two
   lines. Run the new tests and the train/land files' gate tests (R5).
2. **`ungated` (R6).** Test the no-check landing's exit JSON; add the helper and the two keys.
3. **The question (R7).** Test the ungated wording and `land-check` on a no-check base; add the
   `gated` parameter and pass it.
4. **The skill and the words (R8, R9).** Test Step 4; edit SKILL.md (Step 3's `gate` bullet
   also says a train of one is gated), the comments, REFERENCE.md; the spec's grep.

## Tests

- R1: `test_a_train_of_one_is_gated_at_its_tip[still|rebased]` (test_train.py).
- R2: `test_a_train_of_one_whose_commit_fails_the_check_is_ejected` (test_train.py).
- R3: `test_a_green_train_of_one_records_its_tip_gate` (test_train.py), `ungated` null.
- R4: `test_train_run_stops_on_a_hand_written_record[gate-of-one]`, a new parametrization.
- R5: the existing multi-change tests in `tests/test_train.py` and `tests/test_land.py`, unchanged.
- R6: `test_a_landing_with_no_check_says_it_ran_no_gate` (test_train.py).
- R7: `test_the_landing_question_names_only_what_the_batch_holds` gains the ungated case;
  `test_land_check_words_an_ungated_question[no-check|check]` (test_land.py), the
  no-check case with a check in the change's own config, which never stands in.
- R8: `test_land_reports_an_ungated_landing` (test_skills.py).
- R9: the spec's grep, in the report's evidence.

## Rollback

`git revert` of the change's commit undoes all of it. Nothing is written outside the repo: the
extra gate's records live in each landed change's folder history, and they stay harmless after a
revert (a `land-1.gate.md` in a closed change's history is only read by the retrospective's
counts).
