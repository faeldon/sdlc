VERDICT: PASS

The tests cover every requirement, and I found nothing that could not fail. R1 to R19 each map to a test. I did not rerun any test myself.

The gate record, `build/round-1.gate.md`, is green. It shows `2890 passed, 28 skipped in 116.78s`.

Requirement-to-test map:
- **R1, R2, R3:**
  - `test_no_grader_insists_on_a_tool` fails when a `tool_used` grader with `min` ≥ 1 names Read, Write, Edit, Glob or Grep.
  - `test_the_behaviour_case_reads_its_branch_and_says_it_ran` asserts `reads-behaviour` is gone and `says-the-behaviour-check` is an `llm` grader with `focus: trace` that treats Write, Edit and a shell command as equal.
  - The never-grader tests pass unchanged.
- **R4:** `test_a_failed_case_reruns_once_alone` checks `--case` with no `--tag`, a ceiling of 3.75 (5 less the first run's cost), and no third call.
- **R5, R6:** `test_a_case_fails_only_twice`, `test_a_rerun_that_passes_passes_the_run`, and the parametrized `test_a_rerun_the_cap_cant_cover_is_a_failure`, which covers both causes (no ceiling left, rerun stopped at its ceiling).
- **R7:** `test_a_full_run_fails_a_case_on_two_runs` covers 0, 1 and 2 failures, and two environment runs plus one failure.
- **R8:** `test_a_trace_that_could_not_start_git_is_environment` uses the real-trace fixture. It also covers the marker only in the agent's own text, the marker in tool-result text blocks, and a passing run. `test_a_sandbox_failure_is_never_rerun_nor_counted` covers the rest.
- **R9:** `test_only_the_evals_own_workspace_is_removed` covers a workspace in temp (removed), one outside temp (left and listed), and `--keep`.
- **R10:** `test_the_runs_note_is_composed_once` checks the note and that both `CASES_RE` copies match it. `test_a_runs_summary_reads_verdicts_or_its_result` covers both sources.
- **R11 to R15:**
  - `test_factory_cases_writes_the_note_ship_reads_or_stops` covers a failed case writing its note once and a rerun replacing it.
  - `test_factory_cases_skip_writes_why_and_runs_nothing` covers the write and both refusals.
  - `test_a_failed_case_is_a_signal_not_a_refusal` covers the three signals, `by auto` refused, `by person` landing, and the `before` list. It also covers the `cases` part, the question clause, and the no-record fallback.
  - `test_the_dialog_shows_each_failed_or_skipped_case` and `test_the_factorys_reading_of_case_failures_matches_sdlcs` cover the dialog text and the pinned copy of the reading.
- **R16, R17:** `test_no_skill_grants_the_cases`, `test_land_runs_the_cases_before_its_question`, `test_ship_cases_names_the_note_environment_and_rerun`.
- **R18:** `test_full_runs_are_kept_in_order`.

## Notes

- Checks: the one section in `checks.md`, "The docs say how the cases rerun, class the sandbox and land", is a set of `grep` calls on the three docs. It leaves the tree unchanged and fails only if the prose is reverted. I expect it to pass.
- Well covered: R6 exercises both of its causes.
- NIT: tests/test_evals.py:523: the workspace test chmods to 0 and then restores in `finally`. A failure partway through could leave `outside` unreadable for pytest's tmp cleanup. {tests S low}
- Test command: I ran none. The count above is from the gate's record.
