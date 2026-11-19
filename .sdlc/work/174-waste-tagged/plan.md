---
id: 174
slug: waste-tagged
kind: plan
created: 2026-11-19
updated: 2026-11-19
---

# 174 — The retrospective says what a change cost, and what was wasted · plan

> Written by the builder after reading the code; read by the reviewers beside the spec.

## Files to change

- `scripts/metrics.py`: `runtime_trailer()`'s `words()` caps each value at 64 characters, after
  `_model_word()` (R11). No change for R10.
- `plugins/factory/scripts/run_state.py`: `loop_state()` adds `first` (the run's first round, as
  it already computes it) to its output, for `cmd_agent()`.
- `plugins/factory/scripts/factory.py`: `PURPOSES`, `WASTE`, `RERUNNABLE`, `EJECTIONS` and
  `TASK_PURPOSE` beside `COSTS`; `purpose_of()`, pure (R2, R3); `record_cost()` gains `extra`
  fields (`purpose`, `task`, `round` or `land`); `cmd_agent()` works the purpose out before the
  `claude` call, reusing `mend_round()`, `land_round()` and the rows already in `costs.jsonl`.
- `plugins/factory/scripts/landing.py`: `_record_ejection(folder, cause)`, called in
  `_train_eject()` and `_train_stop()` after `_record_land()`, before `_amend_record()` (R4).
- `scripts/factory_records.py`: copies of `PURPOSES`, `WASTE`, `EJECTIONS`; `PARTS`;
  `spend_rows(show, dropped=False)`, pure, reusing `_json_rows()` and `_run_time()` (R5, R6).
- `scripts/retro.py`: `_cost(home, changes, dropped)` over `_records_at()`, `_coverage()` and
  `_share()` (R7–R9); `retro()` adds `cost`; `cmd_retro()` drops `cost.changes` without
  `--metrics`; `_coverage_lines()` and `render_report()` take `cost`; `retro_report()` builds it.
- `tests/test_metrics.py`: R10's two table rows; `test_runtime_values_are_capped` (R11).
- `tests/test_factory.py`: `test_every_task_has_a_purpose`, `test_purpose_by_task_and_round`,
  `test_a_second_run_of_a_step_is_a_rerun`, `test_a_row_names_its_purpose_task_and_round`; the
  existing row-shape assertion in
  `test_each_agent_run_records_its_figures_and_a_resume_is_not_counted_twice` gains the fields.
- `tests/test_train.py`: `test_an_ejection_is_recorded_and_amended_in` (R4).
- `tests/test_retro.py`: `test_row_dollars_sum_to_the_changes_cost`,
  `test_each_row_counts_in_one_part`, `test_retro_reports_cost_per_landed_change_and_waste`,
  `test_the_report_says_how_far_cost_and_waste_rest`; `_drop()` gains `texts`.
- `tests/test_modules.py`: `RECORD_NAMES` gains the new names, `RECORD_FILES` gains
  `ejections.jsonl`.
- `docs/REFERENCE.md` (*Retrospectives*), `plugins/factory/README.md` (the file list),
  `docs/RETRO-SCORECARD.md` (the Cost statuses, wave 3): R12.

## Work order

1. **The nits** (R10, R11): the two table rows, then the cap test red, then the cap.
2. **A row says what it was for** (R1–R3): the pure `purpose_of()` and its tables' tests red, then
   the constants and the function; then `loop_state`'s `first` and `cmd_agent()`'s fields, with
   `test_a_row_names_its_purpose_task_and_round` red first through the fake `claude`.
3. **An ejection is recorded** (R4): the train test red, then `_record_ejection()` in both places.
4. **Per-row dollars and parts** (R5, R6): the two pure tests on `spend_rows()` red, then the
   function and its copies; `test_modules.py`'s lists updated with it.
5. **Retro's `cost` block** (R7, R8): the scratch-repo test red, then `_cost()` and `cmd_retro()`.
6. **The trust band** (R9): the report test red, then the two coverage lines.
7. **Docs** (R12).

## Tests

- R1: `test_every_task_has_a_purpose`, `test_a_row_names_its_purpose_task_and_round`.
- R2: `test_purpose_by_task_and_round`.
- R3: `test_a_second_run_of_a_step_is_a_rerun`.
- R4: `test_an_ejection_is_recorded_and_amended_in`.
- R5: `test_row_dollars_sum_to_the_changes_cost`.
- R6: `test_each_row_counts_in_one_part`.
- R7, R8: `test_retro_reports_cost_per_landed_change_and_waste`.
- R9: `test_the_report_says_how_far_cost_and_waste_rest`.
- R10: two rows in `test_a_command_ending_in_a_lone_ampersand_goes_to_the_background`'s table.
- R11: `test_runtime_values_are_capped`; `test_runtime_trailer_round_trips` still passes.
- R12: by review; `./check.sh` covers the docs' shape.
- Contracts: `test_every_shared_name_is_the_factorys` pins the new copies;
  `test_no_factory_record_is_named_outside_its_reader` keeps `ejections.jsonl` out of `retro.py`.

## Rollback

`git revert` undoes all of it. What it leaves: rows written by factory runs after this change carry
`purpose`, `task` and `round`/`land`, and an ejected change may hold `runs/ejections.jsonl`. Both
are extra JSON fields or a file no reverted reader looks at, so nothing breaks; nothing outside
the repo is written and nothing is published.
