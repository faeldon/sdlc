VERDICT: PASS

I mapped every requirement to a test that fails without it. I read the tests and the gate's record. I did not run anything. The gate's record, `build/round-1.gate.md`, is green.

## Notes

- **R1:** `test_every_task_has_a_purpose` covers every name in `TASKS`. `test_a_row_names_its_purpose_task_and_round` drives `cmd_agent` with `claude` faked. It checks the exact row fields and that a loop task's row carries no `land`. It also checks that a second review in the same round is tagged `rerun`.
- **R2:** `test_purpose_by_task_and_round` is a 23-row table. It covers the restart case (`first=3`) and `approve` in round 3.
- **R3:** `test_a_second_run_of_a_step_is_a_rerun` covers another role, another round, a second `fix`, a second `resolve`, a landing `rerun`, and legacy rows with no task.
- **R4:** `test_an_ejection_is_recorded_and_amended_in` covers the eject path and the stop path. For the eject it checks that the row is in the commit, that `costs.jsonl` is byte-identical, and that the tree is clean. For the stop it checks that only the moved changes get a row.
- **R5:** `test_row_dollars_sum_to_the_changes_cost` checks the resumed builder, the unknown row, the floor-at-0 case and an empty `show`. The six row dollars are `[0.5, 0.25, None, 0.5, 0.2, 0.3]`, which sum to `fr.cost()["usd"]`.
- **R6:** `test_each_row_counts_in_one_part` checks the order of the parts and the sum of the parts. It also checks that an untagged row of a dropped change is not waste.
- **R7, R8:** `test_retro_reports_cost_per_landed_change_and_waste` uses hand-worked values. The fixture covers a rework and a mend, an ejected-then-landed change, a dropped change, a hand-built change, an old change with no `purpose`, a factory change with no rows and one with no cost. It asserts `per_change`, the missing reasons, the waste parts, `by_role`, `by_model` and `untagged`. It also checks that retro changes nothing in the repo. A separate test pins that `cost.changes` appears only with `--metrics`. The existing lean-versus-full equality test was updated to match.
- **R9:** `test_the_report_says_how_far_cost_and_waste_rest` checks both Coverage lines, the untagged count and the greying under half.
- **R10, R11:** the two `curl` cases are in the table. `test_runtime_values_are_capped` checks both values at 64 characters and that the line reads back.
- **R12:** docs, checked by review, not by a test.
- The gate recorded 3191 passed and 29 skipped.
- `checks.md` doesn't exist, which is fine, because no requirement needed an acceptance check.

- NIT: tests/test_factory.py: R1's `land` field is never asserted on a row written by `cmd_agent` for a landing task. `purpose_of` is tested for it, but no test runs a `land-review` through `cmd_agent` and checks the row carries `land`. {tests S low}
- NIT: tests/test_train.py: the stop half of `test_an_ejection_is_recorded_and_amended_in` doesn't check `at` or `land` on its rows. Only `cause` is asserted. {tests S low}
