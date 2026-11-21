I built the change: when CI on the base branch's tip is red, `status` says so, ship's question says so, and the factory's landing treats it as a signal. The full gate passed (3895 passed, 29 skipped, exit 0) and everything is left uncommitted. HEAD is still `1c740dd`.

## Slices built

1. **The tracker reads CI (R1, R11).** In `trackers/github.py`, a pure `ci_state(runs)` sorts runs into red, pending, green or unknown, and `Tracker.ci(branch, sha, timeout)` makes the one `gh run list` call. A failed, hanging or unparsable `gh` reads as `unknown`, never red. `_gh()` now takes a `timeout` and is otherwise unchanged. The fake `gh` in `tests/conftest.py` now answers `run list`, and can fail (`FAKE_GH_FAIL=run`) or hang (`FAKE_GH_SLEEP`).
2. **Core's reading and its cache (R2, R3, R6).** `base_ci()` reads the tip from the remote-tracking ref. Its readings are cached in `sdlc-ci.json` in the git common dir, keyed by branch and sha and written with a temp file and `os.replace`. A tracker that raises reads as `unknown` and nothing is cached for it. `ci_problem()` words the Problems entry.
3. **Status (R4, R5).** The entry is added in `cli_status()` beside the `git.base` one, using `CI_EVERY` (600 s). `vet` never reads CI.
4. **Preflight and ship's question (R7, R8).** Preflight gains a `ci` part, read with `CI_FRESH` (60 s) after the problems are collected, so a red base never refuses. `ship_question()` gets the clause `on a base whose CI is red at <sha> (<url>)`, and `cmd_ship_question()` reads CI itself. I also updated the docstrings and `READ_ONLY`'s comment to say the CI cache is the one thing they write.
5. **The landing's signal (R9).** `land_signals()` adds `CI on <branch> is red at <sha>: <url>`.
6. **Docs (R10).** CONTRIBUTING *Writing a tracker* lists `ci()`. REFERENCE *Trackers* gains a *CI on the base branch* paragraph. AGENTS *Updates* now names two no-WAIT writes, the update cache and `CI_CACHE`. `checks.md` holds three acceptance checks for these doc lines.

## Tests added
- `tests/test_base_ci.py` (new):
  - **R1:** `test_github_ci_reads_each_state`, `test_bad_json_is_unknown`, `test_a_hanging_gh_is_unknown`.
  - **R11:** `test_ci_state_classifies_runs` (marked `portable`, 9 cases).
  - **The copied failure words:** `test_core_reads_failures_by_the_trackers_words` pins core's `CI_FAILED` to the tracker's `CI_RED`.
  - **R2:** `test_base_ci_never_calls_the_tracker_without_a_source` (4 cases), `test_base_ci_without_a_base_branch_is_unknown`.
  - **R3:** `test_base_ci_reuses_the_cache_for_the_same_tip`, `test_an_old_or_future_cache_is_read_again`.
  - **R6:** `test_a_raising_tracker_reads_as_unknown`.
  - **R5:** `test_the_tracker_is_given_ci_timeout`, `test_status_with_a_fresh_cache_calls_nothing`.
  - **R4:** `test_status_names_a_red_base`, `test_status_is_silent_on_green_pending_and_unknown`, `test_vet_strict_never_sees_ci`.
  - **R8:** `test_ship_question_names_a_red_base`, `test_ship_question_command_reads_ci_itself`.
- **R7:** `tests/test_preflight.py::test_preflight_reports_ci_and_never_refuses_on_it`.
- **R9:** `tests/test_land.py::test_a_red_base_is_a_signal` checks the signal and that `land-check`'s `clear` turns false. `test_an_unknown_base_is_no_signal` covers unknown, pending and green.

Each failed before its code was written: the new file errored with no `CI_EVERY`, then the ship tests failed with no `ci` keyword, preflight failed with `KeyError: 'ci'`, and the landing test got an empty signal list.

## Changes to plan.md
- `_gh()` keeps its decoding; I dropped `errors="replace"` so no other `gh` call changes.
- `base_ci()` checks the target and whether the tracker has `ci()` before it reads the cache, so a repo that turned its tracker off never shows an old red reading. The spec read the cache first. `unavailable()` runs only when the cache misses.
- The Tests section lists the four tests I added beyond the plan.

I left the example sentence in ship's `SKILL.md` alone: it already leaves out several clauses, so it isn't a full list. Nothing went into `notes.md`. I ran the full gate twice by mistake; the second run was only to capture its exit code.

- UNTESTABLE: none

No decisions raised this round.

## Evidence

$ uv run --group dev pytest -q tests/test_base_ci.py -n auto
2 failed, 29 passed in 2.30s
exit: 1

$ uv run --group dev pytest -q tests/test_preflight.py -k ci
FAILED tests/test_preflight.py::test_preflight_reports_ci_and_never_refuses_on_it
1 failed, 61 deselected in 0.23s
exit: 1

$ uv run --group dev pytest -q tests/test_preflight.py tests/test_base_ci.py -n auto
93 passed in 2.54s
exit: 0

$ uv run --group dev pytest -q tests/test_land.py -k "red_base or unknown_base"
FAILED tests/test_land.py::test_a_red_base_is_a_signal - AssertionError: []
1 failed, 1 passed, 98 deselected in 1.99s
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k "red_base or unknown_base"
2 passed, 98 deselected in 2.41s
exit: 0

$ uv run --quiet --script scripts/sdlc.py accept 220
  "passed": true,
  "problems": []
exit: 0

$ uv run --group dev ruff check . --output-format concise
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
338 files already formatted
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_base_ci.py tests/test_preflight.py tests/test_windows.py tests/test_modules.py tests/test_nothing_local.py tests/test_feature_map.py tests/test_findings.py tests/test_update.py
339 passed in 5.17s
exit: 0

$ uv run --group dev pytest -q tests/test_land.py -k "red_base or unknown_base"
2 passed, 98 deselected in 2.18s
exit: 0

$ uv run --group dev pytest -q -m portable tests/test_base_ci.py
9 passed, 22 deselected in 0.02s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 220
All checks passed!
3895 passed, 29 skipped in 234.27s (0:03:54)
✔ Validation passed
exit: 0

$ git log --oneline -1
1c740dd File 2026-11-21-46
exit: 0
