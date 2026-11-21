VERDICT: PASS

I found no requirement without a test that would fail if the code were absent. The gate's record (`build/round-1.gate.md`, attempt 1) is PASS: `./check.sh` exited 0, and `claude plugin validate --strict` passed.

## Notes

**Requirement map**
- **R1:** `test_sdlc_loads_nothing_from_plugins` was changed. It pins `hooks/` to `hooks.json` alone, the exact `SessionStart` hook with matcher `startup` and the literal command, and a timeout of 30 or less. The existing manifest assertion at `tests/test_skills.py:1175` rejects a `hooks` key in `plugin.json`.
- **R2:** `test_hook_is_silent_when_it_can_t_tell` covers no `claude`, a failing `ls-remote`, running outside a repo, and a check that raises. Each time the hook exits 0 and prints nothing.
- **R3:** the two line forms are tested character for character in `test_the_line_*`. The silent cases are tested too: no release, no installs, current, downgrade, and a folder-read install.
- **R4:** `test_one_check_a_day`, `test_a_stale_cache_is_checked_again` and `test_a_failed_check_is_cached_as_null` cover the daily cap. They also check that the cache dirties no checkout and that a failed check is cached as `latest: null`.
- **R5:** `test_in_place_is_never_told` adds `.git` to the plugin root. It asserts no hook line, no nudge, `in_place` true, no steps and no network call.
- **R6:** the parse test and the resolved-path test cover this. The row set includes a worktree of this repo and another repo's install.
- **R7:** `test_status_reads_the_cache_alone` covers it. It asserts the line from a fresh cache, no network argv, and silence for a null, stale or missing cache.
- **R8:** `test_steps_in_order`, `test_no_steps_when_everything_is_current` and `test_update_refreshes_the_day_s_cache` cover it. The `elsewhere` and worktree cases are covered.
- **R9:** the two `test_installed_*` tests cover it, plus the no-network, no-cache-write test.
- **R10:** `test_update_is_not_read_only` covers `READ_ONLY` and `ALLOW_RULES`. The AGENTS.md paragraph is covered by the check below.
- **R11:** `test_skills.py` covers the `GATED`, `READS_CONFIG` and `allowed-tools` rules. The new skill test covers the WAIT text and the exact `claude` commands, and requires that none run before the WAIT. It also requires no commit or push, and the restart and setup text after the WAIT.
- **R12:** `test_readiness_lists_the_uncommitted_paths_setup_owns` and `test_setup_refuses_a_stale_session_and_names_the_commit` cover it.
- **R13:** `test_hook_end_to_end` covers it. It runs `uv run` on a copy of the script, against the fake `claude` and a bare repo. It asserts the exact line, then asserts that a second run the same day makes no second `claude` call, even after a newer tag was pushed. It is not marked `portable`, as the spec asked.
- **R14:** the fixture carries `printed_by: Claude Code 2.1.311`, uses neutral paths, and `test_nothing_local` scans it.
- **R15:** `test_docs_list_the_five_steps_in_order` (README and REFERENCE) and `test_the_maps_name_the_hook_and_the_command` cover it.
- **R16:** `test_windows.py` is unchanged and passed in the gate.

**Checks in `checks.md`**
- *AGENTS.md maps the hook and its cache (R10):* greps for the paragraph's heading, `hooks/hooks.json`, `sdlc-update.json` and the "That cache is the one write" phrase. It would fail if the paragraph were removed, and it leaves the tree unchanged. I expect it to pass, and did not run it.
- *README's skill table lists /sdlc:update (R15):* greps for the table row. It would fail without the row and leaves the tree unchanged. I expect it to pass, and did not run it.

**Tests run:** `uv run --group dev pytest -q tests/test_update.py tests/test_readiness.py::test_readiness_lists_the_uncommitted_paths_setup_owns` gave 24 passed, run in the foreground. I did not run the whole suite.

- NIT: tests/test_update.py:107: the fake `claude` opens its log and rows files without an encoding, unlike the `encoding="utf-8"` the repo's tests use elsewhere. It is not a portable test, so it only matters on a non-UTF-8 locale. {tests S low}
