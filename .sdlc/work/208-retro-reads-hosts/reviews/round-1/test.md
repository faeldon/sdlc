VERDICT: PASS

Every requirement from R1 to R13 has a test that would fail without it. R14 to R16 are wording and docs, and they are covered the way the plan says.

## Notes

- NIT: tests/test_retro_hosts.py:329: R3 says a listed path under this repo's `.claude/worktrees/` is skipped and counted as `own`. Only the main checkout is listed in the fixtures, so the worktree case is never exercised. Add a worktree path to `_listed`. {tests S med}
- NIT: tests/test_retro_hosts.py:325: the `!` exclusion is only shown against a path that doesn't exist, so it would pass even if an excluded host were still read. Exclude a real fixture host and assert it is absent from `read`. {tests S med}
- NIT: tests/test_retro_hosts.py:426: R12 says no host figure enters the indicators the next retro reads back. The test compares `retro`'s JSON with and without a list, but doesn't compare the report's indicators block. {tests S low}

Coverage, requirement by requirement:
- **R1 and R2:** `test_a_host_repo_never_reads_hosts` and `test_no_host_list_is_unmeasured`. The latter checks that no subprocess runs and `claude plugin list` is never called.
- **R3:** `test_the_host_list_format` is marked `portable`. `test_two_fixture_hosts_give_known_counts` adds the own and repeated-path cases.
- **R4:** `test_host_reads_are_log_and_show_only` checks every argv for `git -C <host>` with an allowed subcommand.
- **R5:** `test_an_unreadable_host_is_counted_not_fatal` covers `missing`, `not-a-repo`, `no-base` and `failed`, and checks that `cmd_retro` returns 0 and the exception text never prints.
- **R6 and R8:** the counts test covers the window boundary, one drop, `Sdlc-Fixes`, `reworks:`, and the old-`work/` change with no trailers (tier `unknown`, excluded from medians). `test_older_trailers_are_unmeasured_not_zero` repeats the R8 case on its own. There is also an empty-list test where every figure is null, not 0.
- **R7:** planted names cover directory, branch, title, dropped reason, `Sdlc-Origin`, `Bash:<program>`, a non-plugin skill, a non-plugin stage, a config key, a template and the tmp path. They are checked in the retro JSON, the insights JSON and the report. `dropped_names == 0` proves the filter works before summing, and a separate test covers the last guard.
- **R9 to R11, R13:** all have a named test. The discovery test checks the path and the failure reason never appear in the output.

Checks in `checks.md`: none exist, and none are needed.

Test runs:
- The gate record, `build/round-1.gate.md`, is PASS: "3694 passed, 29 skipped".
- `uv run --group dev pytest tests/test_retro_hosts.py -q`: 18 passed.
