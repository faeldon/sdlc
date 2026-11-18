VERDICT: PASS

Every requirement from R1 to R12 maps to a named test that exists. I did not revert code to confirm each test fails without it; I judged that from reading the assertions against the diff. The full suite passes.

## Notes

- **R1 to R12 coverage:** the spec and plan list 21 test names, and all 21 exist in the files they name.
  - R1 is covered in `test_sdlc.py`; R4 and R7 in `test_indicators.py`.
  - R2, R3, R5, R6, R8, R9, R10 and R12 are in `test_retro.py`; R11 is in `test_skills.py`.
- **Tests that can fail:**
  - `test_test_times_get_their_own_limits` can fail. It shrinks the evidence limits to 10 characters and 0.2 s. It then reads a report through `_times()` with a `sleep 0.5`, and checks that plain `_evidence()` times out at the same settings.
  - `test_nothing_but_retro_runs_test_times` can fail. It runs `check`, `status`, `config`, `readiness` and `retro --report`, and each must leave no marker file. A final `retro()` call must leave one.
  - `test_due_is_slow_or_drifted` exercises both `due` paths separately: slow alone, with `drifted == []`, and drifted alone, with times unset.
  - `test_retro_with_test_times_writes_nothing` compares the tree before and after a real `cat` of a committed report.
  - `test_retro_commit_refuses_a_changed_test_file` checks for the specific "also changed: tests/test_drafts.py" refusal.
- **Departures from the spec:**
  - A `time` of 0 now reads as `None` (untimed), where the spec said `seconds` is never 0.
  - `drifted_tests` treats a missing `present` set as every test file being present.
  - Both are recorded in the plan.
  - `junit_times` returns the same `cases` / `error` shape either way, so the tests are unaffected.
- **Not yet confirmed:** the spec's manual check of this repo's own JUnit file has not run. That means running pytest with `--junitxml`, passing the file to `junit_times()`, and comparing the count to pytest's summary. The suite doesn't cover it.
- **`checks.md`:** the change has none, so there are no checks to judge.
- **Command run:** `uv run --group dev pytest -q -n auto`, which gave 2364 passed, 13 skipped.

- NIT: tests/test_retro.py:1668: the `# fmt: skip` blocks keep hand-aligned dicts. This is a style choice, not a defect.
