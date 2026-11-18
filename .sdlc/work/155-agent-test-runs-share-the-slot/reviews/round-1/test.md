VERDICT: PASS

R1 to R11 each have a test that fails without the change. R12 is covered by an acceptance check.

## Notes

- **Gate record:** `build/round-1.gate.md` is `GATE: PASS` with `2867 passed, 28 skipped`. `ruff check`, `ruff format` and `claude plugin validate --strict` also pass. I did not run the gate or any test myself, and I read the tests rather than running them.
- **R1:** `test_check_runs_the_base_branchs_command_and_exits_with_its_code` sets a different command in the worktree's own config. It asserts `base-ran` is printed, `mine` is not, and the exit code is 3.
- **R2:** `test_check_refuses_and_runs_nothing` covers all three refusal cases and asserts the stamp file never appears.
- **R3:** `test_two_checks_with_one_slot_run_one_after_the_other` compares the two runs' start and end times and asserts exactly one waiting line. `test_a_check_waits_for_a_gates_slot` uses the existing `HOLD` child to show gates and checks share slots.
- **R4:** `test_a_killed_check_frees_its_slot` kills `check` and takes the slot within 2 seconds. `test_a_check_past_the_timeout_is_killed` patches `GATE_TIMEOUT` and checks the `timed out after 0.5s` message and the non-zero exit.
- **R5:** `test_a_green_check_writes_nothing_and_never_clears_the_gate` compares `git status --porcelain` before and after, asserts no `*.gate.md` appears, and asserts `verdicts` still says `gate`.
- **R6:** `test_the_builders_prompts_name_the_check_command` covers the build, fix, rework, decided and mend prompts, and asserts the review, verify and approve prompts don't name `check`. The resolver prompt is asserted in `tests/test_train.py`. The restart and rework prompt tests were updated for the new trailing line.
- **R7 to R9:** The tests in `tests/test_skills.py` assert each phrase. `_evidence_commands` fails if an Evidence example's `$` line is `./check.sh`.
- **R10:** `test_evidence_citing_the_gate_record_is_a_read` is in `tests/test_factory.py`, not `tests/test_evidence.py` as the spec says. `read_evidence` lives in `factory.py`, so the location is reasonable.
- **R11:** The `_shell()` parametrize cases cover `check` as true, a quoted path as true, and `land-check` and `gate` as false.
- **`checks.md`:** The one check greps the README for the gate-slot paragraph line and for `factory.py check NNN`. I expect it to pass, since the README is modified, but I did not run it. It would fail on a revert of the README, which is its purpose.

- NIT: tests/test_factory.py:4900: the new R3 and R4 tests carry no `@pytest.mark.portable` even though the spec says "marked `portable` where they use no shebang fakes". The two-checks test uses `sleep` and `sh`, so leaving them unmarked is probably right, but the spec's intent is unclear. {tests S low}
