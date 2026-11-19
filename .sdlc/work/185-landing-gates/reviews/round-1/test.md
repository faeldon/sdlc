VERDICT: PASS

Every requirement R1–R19 has a named test that exists and asserts the behaviour the spec describes. R20 is covered by an acceptance check in `checks.md`. I did not run any test myself, so the results below come from the gate's record and my reading of the tests. The gate record, `build/round-1.gate.md`, is `GATE: PASS`, `./check.sh` exit 0, tree unchanged. It reports `3381 passed, 29 skipped in 160.90s`, and `claude plugin validate --strict` passed.

## Notes

- **R1–R4, R6–R9 (clearance and approver):**
  - The loop tests (`test_unchanged_checks_run_as_stacked_without_a_stop`, `test_a_changed_check_off_the_list_stops_before_the_approver` and others) drive a real train with a fake `claude`.
  - R4 checks that no approver call happens and that `land-accept.md` holds only one attempt. R2 checks that the two attempts sit on different stacked commits. Both would fail if `accept` ran when it shouldn't, or didn't run when it should.
  - `test_the_approvers_answer_decides_a_changed_check` has one case each for harmless, escalate, unreadable, disagreeing, preamble, missing and stale.
  - `test_harmless_never_clears_a_command_off_the_list` and `test_the_loop_rechecks_before_it_runs_accept` assert on `_run_plan` directly.
- **R5:** `test_read_only_command_passes` and `test_read_only_command` are parametrized, each refusal case naming its reason, and marked portable.
- **R11–R16 (build):**
  - The R11 test proves the base branch's command runs and not the checkout's, using a `touch` marker.
  - R13 checks that a train of one lands with `build/land-1.build.md` in its commit.
  - R14 checks the reason text, that there is exactly one `train: build` run (so no bisect), and that nothing is ejected.
  - R12 is parametrized over a base with no build, `build_when` unset, a match, a miss, a sensitive path and an invalid regex.
  - R15 and R16 cover the cases where the build must not run.
- **R10, R17, R18:** each is an extension of an existing test, with the specific cases asserted.
- **R19:** `test_a_run_with_no_figures_leaves_the_next_try_its_own_purpose` asserts that the first run writes no row and that the second run's purpose is `build`, not `rerun`.
- **Check in `checks.md`:** "The docs state the landing's new gates" (R20). I expect it to pass on the current tree. It would fail on a revert, since it needs the new names and rejects the old wording. It writes nothing, so the tree stays unchanged. I did not run it.
- **R17 nit:** `tests/test_land.py` asserts `count(ALREADY) <= 1` across the refusals. That is slightly looser than "exactly once where the answer is missing", but it is what the spec asks for.

- NIT: tests/test_train.py:2307: the R9 test drives a real train to `accept` and then edits `checks.md`. The edited command is `rm -f bb.txt`, which is off the list, so it never exercises the case where an edit passes R5 but loses the approver's clearance. {tests S low}

Test command: none run by me; the count comes from the gate's record above.
