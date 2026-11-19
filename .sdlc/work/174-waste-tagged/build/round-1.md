I built change 174 and left it uncommitted for `/sdlc:ship`. This time the full gate run finished green: ruff, formatting, 3191 tests passed (29 skipped) and plugin validation.

**Slices built**
1. **Nits (R10, R11).** The two URL `&` cases went into the existing table and passed with no code change, which pins the current behaviour. `runtime_trailer()` now cuts each value to 64 characters (`RUNTIME_CAP`) after `_model_word()`, so the trailer's format doesn't change.
2. **Each row says what it was for (R1–R3).**
   - `factory.py` gains `PURPOSES`, `WASTE`, `RERUNNABLE`, `EJECTIONS`, `TASK_PURPOSE`, `ROUND_PURPOSE`, a pure `purpose_of()` and `cost_rows()`.
   - `cmd_agent()` works out the purpose before the `claude` call, and `record_cost()` writes `purpose`, `task`, and `round` or `land`.
   - `run_state.loop_state()` now outputs `first`, the run's first round.
3. **Ejections are recorded (R4).** `landing._record_ejection()` appends `{at, land, cause}` to `runs/ejections.jsonl`. `_train_eject()` and `_train_stop()` call it before `_amend_record()`, so the row ends up in the change's commit.
4. **Per-row dollars and parts (R5, R6).** `factory_records.spend_rows(show, dropped)`: each row's dollars are the change in its session's running total, floored at 0, so a resumed builder counts once. Each row lands in one part, in the spec's order. `PARTS` is core's own name; the copies of the factory's names are pinned by the existing test.
5. **Retro's `cost` block (R7, R8).** `retro._cost()` gives `per_change`, `waste`, `by_role`, `by_model`, `unknown`, `untagged` and `changes`, each with its coverage. A change with no dollars is counted missing, never $0. `cost.changes` is printed only with `--metrics`.
6. **The trust band (R9).** The report gains two coverage lines, `cost per landed change` and `waste share`; the waste line also says `N runs untagged`.
7. **Docs (R12).**
   - `docs/REFERENCE.md` *Retrospectives* describes `cost`.
   - The factory README's file list gains the new row fields and `runs/ejections.jsonl`.
   - `docs/RETRO-SCORECARD.md` marks the three Cost statuses captured (S4, 174) and S4 done in wave 3.

**Tests added**

| Requirement | Test |
|---|---|
| R1 | `test_every_task_has_a_purpose`, `test_a_row_names_its_purpose_task_and_round` (through a fake `claude`) |
| R2 | `test_purpose_by_task_and_round` (23 cases) |
| R3 | `test_a_second_run_of_a_step_is_a_rerun` |
| R4 | `test_an_ejection_is_recorded_and_amended_in` (an eject and a stop) |
| R5 | `test_row_dollars_sum_to_the_changes_cost` |
| R6 | `test_each_row_counts_in_one_part` |
| R7, R8 | `test_retro_reports_cost_per_landed_change_and_waste` (figures worked out by hand), `test_retro_prints_each_changes_cost_only_with_metrics` |
| R9 | `test_the_report_says_how_far_cost_and_waste_rest` |
| R10 | two rows in the `&` table |
| R11 | `test_runtime_values_are_capped` |

**Existing tests I changed**
- The row-shape assertion in `test_each_agent_run_records_its_figures…` gains the new fields.
- The landing-steps test in `tests/test_land.py` checks a landing row's `land` field.
- The `--metrics` test pops `cost.changes`, as it already pops `spend.changes`.
- The greyed-headline test expects the two new coverage lines.
- `test_modules.py`'s name and file lists gain the new names and `ejections.jsonl`.
- `_drop()` in the retro tests gains a `texts` argument.

**Seen failing first, and not**
- These tests failed for the expected reason before their code was written: the purpose tests, the ejection test, `spend_rows`, retro's `cost` block, the report test and the runtime cap. The failing runs are in the first report.
- The `land` field check in `tests/test_land.py` was written after the code, so I never saw it fail.

**`plan.md`**: written before the code. The build followed it apart from two small additions: `cost_rows()`, so `cmd_agent` reads the earlier rows, and an optional `note` on `_coverage_line()` for the untagged count. **`notes.md`**: nothing added.

- DECISION: [default] A `decided` run's row uses `state["round"]`, falling back to `state["built"]`, because `loop_state` names no round while it waits on a decision. Going ahead with that.
  - OPTION: round or built — puts the answer in the round it builds on, so a later round's answer counts as rework; the cost is that it relies on a fallback
  - OPTION: no round on the row — simplest; but a `decided` run would always be tagged `build`, and the rework it does after round 1 wouldn't count as waste
  - WHY: R2 says `decided` is `build` in the run's first round and `rework` after it, which needs a round to compare.
- DECISION: [default] The waste line's untagged count is the number of runs (`2 runs untagged`); the changes those runs belong to are already named in its missing-reasons. Going ahead with that.
  - OPTION: runs — says how much spend sits outside every share
  - OPTION: changes — duplicates the missing-reason count already on the line
  - WHY: R9 asks the line to name the untagged count, and the change count is already there.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q -n 4 tests/test_factory.py tests/test_modules.py tests/test_metrics.py tests/test_retro.py::test_row_dollars_sum_to_the_changes_cost tests/test_retro.py::test_each_row_counts_in_one_part tests/test_retro.py::test_retro_reports_cost_per_landed_change_and_waste tests/test_retro.py::test_retro_prints_each_changes_cost_only_with_metrics tests/test_retro.py::test_the_report_says_how_far_cost_and_waste_rest tests/test_retro.py::test_retro_prints_each_change_s_numbers_only_when_asked tests/test_retro.py::test_the_report_greys_a_thin_headline tests/test_train.py::test_an_ejection_is_recorded_and_amended_in tests/test_train.py::test_a_stopped_train_puts_every_unlanded_change_back tests/test_land.py::test_a_landing_records_each_step_it_takes
626 passed in 127.99s (0:02:07)
exit: 0

$ uv run --group dev pytest -q -n 4 tests/test_board.py -k "cost or step or time"
152 passed, 28 skipped in 5.98s
exit: 0

$ uv run --group dev ruff format --check .
312 files already formatted
exit: 0

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 174
All checks passed!
312 files already formatted
3191 passed, 29 skipped in 178.00s (0:02:58)
✔ Validation passed
exit: 0
