VERDICT: PASS

Every requirement from R1 to R11 has a test that fails without it, apart from the small gaps in Notes.

## Notes

- NIT: tests/test_base_ci.py: R3 says nothing is written outside a repo, and only the missing-source cases check for a cache file. No test calls `base_ci()` with a home that isn't a repo and asserts it writes nothing. {tests S low}
- NIT: tests/test_base_ci.py: the `os.replace` temp-file write and `newline="\n"` (R3, R11) are covered only by the existing `tests/test_windows.py` scans, not by a test of this change. {tests S low}
- NIT: tests/test_land.py::test_a_red_base_is_a_signal: the final `clear is False` assertion monkeypatches `_preflight`. It proves `clear` reads the signal, but not that the real preflight reaches `land_signals()` with the `ci` part. {tests M low}

**Coverage**
- **R1, R11:** `test_ci_state_classifies_runs` is `portable` and covers red, pending, green, cancelled, neutral, timed_out and startup_failure. `test_github_ci_reads_each_state` covers the other-sha drop, empty, a failed `gh` and the exact argv. `test_a_hanging_gh_is_unknown` and `test_bad_json_is_unknown` cover the timeout and bad JSON.
- **R2:** one parametrized case per missing source, plus the missing `git.base`. Each asserts that the `gh` fake recorded no call and that no cache file was written.
- **R3:** reuse for the same tip, a moved tip, an old cache, a future-dated cache and a corrupt cache.
- **R4:** `test_status_names_a_red_base` checks the exact line. `test_status_is_silent_on_green_pending_and_unknown` and `test_vet_strict_never_sees_ci` cover the other states and `vet`.
- **R5:** `test_status_with_a_fresh_cache_calls_nothing` and `test_the_tracker_is_given_ci_timeout`.
- **R6:** `test_a_raising_tracker_reads_as_unknown` checks the `unknown` reading, no cache written, and no traceback from `status`.
- **R7, R8, R9:** `test_preflight_reports_ci_and_never_refuses_on_it` checks the part's shape and that problems and the exit code are unchanged. `test_ship_question_names_a_red_base` and `test_ship_question_command_reads_ci_itself` cover the clause. `test_a_red_base_is_a_signal` and `test_an_unknown_base_is_no_signal` cover the landing signal.
- **`CI_FAILED` copy:** `test_core_reads_failures_by_the_trackers_words` pins it to the tracker's `CI_RED`.

**Acceptance checks in `checks.md`** (read, not run)
- The tracker interface lists `ci()` as optional: a grep for the new line in `docs/CONTRIBUTING.md`. I expect it to pass with the change and fail without it. It is read-only.
- REFERENCE.md says what a red base shows: two greps on the new paragraph in `docs/REFERENCE.md`. Same expectation, and it leaves the tree unchanged.
- AGENTS.md names the CI cache: a grep for the CI cache line, plus a check that the old "one write" sentence is gone. Same expectation, and it leaves the tree unchanged.

**Run**
- The gate record `build/round-1.gate.md` shows `3895 passed, 29 skipped`, and plugin validation passed.
- I ran `pytest -q tests/test_base_ci.py`: 31 passed.
