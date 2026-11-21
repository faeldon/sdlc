---
id: 220
slug: base-ci-red
kind: plan
created: 2026-11-21
updated: 2026-11-21
---

# 220 — A red CI on the base branch shows where the person looks · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/trackers/github.py`: `CI_RED`, `CI_FIELDS`, a pure `ci_state(runs)`, and
  `Tracker.ci(branch, sha, timeout)`. `_gh()` gains a `timeout` keyword, and its decoding is
  unchanged for every other call; `ci()` catches `OSError` and `subprocess.TimeoutExpired` itself.
- `scripts/sdlc.py`, beside the updates section: `CI_CACHE`, `CI_EVERY`, `CI_FRESH`, `CI_TIMEOUT`,
  `CI_STATES`, `CI_FAILED` (the interface's failure words, a copy of the tracker's `CI_RED`, pinned
  by a test), `_ci_cache_path()`, `_read_ci_cache()`, `base_ci()`, `ci_problem()`. It reuses
  `_ledger_dir()` (as `_update_cache_path()` does), `tracker()`, `_git()`, and the temp-file and
  `os.replace` write `check_update()` uses. `base_ci()` checks the target and whether the tracker
  has `ci()` before it reads the cache, so a repo that turned its tracker off never shows an old
  red reading. It runs `unavailable()` only when the cache misses, just before the network call.
  - `cli_status()`: appends `ci_problem(base_ci(home, cfg, CI_EVERY), remote)` beside the
    `git.base` entry.
  - `cmd_preflight()`: a `ci` part, `base_ci(home, cfg, CI_FRESH)`. It stays out of the problems
    loop and out of `SHIP_BRANCHES`. Its docstring says the one write is that cache.
  - `ship_question()`: a `ci` keyword and its clause after the sensitive-path one;
    `cmd_ship_question()` passes `base_ci(home, cfg, CI_FRESH)`.
  - `READ_ONLY`'s comment: a state cache in the git common dir is allowed.
- `plugins/factory/scripts/landing.py`: `land_signals()` adds the red-base signal from `pre["ci"]`.
- `tests/conftest.py`: the fake `gh` answers `run list` from `st["runs"]`, fails on
  `FAKE_GH_FAIL=run`, and hangs for `FAKE_GH_SLEEP` seconds.
- `tests/test_base_ci.py` (new): R1–R6, R8, R11, and the copy pin.
- `tests/test_preflight.py`: R7.
- `tests/test_land.py`: R9.
- `docs/CONTRIBUTING.md` *Writing a tracker*, `docs/REFERENCE.md` *Trackers* and *After an
  update*, `AGENTS.md` *Updates*: R10.
- `.sdlc/work/220-base-ci-red/checks.md` (new): R10's doc lines, as acceptance checks.

## Work order

1. **The tracker reads CI** (R1, R11). Fake `gh run list`, then `ci_state()` and `Tracker.ci()`,
   tested by driving the fake through each state, a failed `gh`, a timeout and bad JSON.
2. **Core's reading and its cache** (R2, R3, R6). `base_ci()` with each missing source, the cache
   reused for the same tip and read again for a moved one, an old or future-dated cache, and a
   raising tracker.
3. **Status** (R4, R5). The Problems entry on red, silence on the rest, `vet --strict` unchanged,
   and a fresh cache calling nothing.
4. **Preflight and ship's question** (R7, R8). The `ci` part, never a problem, and the clause.
5. **The landing's signal** (R9). `land_signals()` with a red `pre["ci"]`, and with unknown.
6. **The docs** (R10), and `checks.md` for them.

## Tests

- R1: `test_github_ci_reads_each_state` (red, pending, green, cancelled-is-green, empty is
  unknown, a failed `gh` is unknown, a run on another sha is dropped),
  `test_a_hanging_gh_is_unknown`, `test_bad_json_is_unknown`.
- R11: `test_ci_state_classifies_runs`, marked `portable`; `tests/test_windows.py` unchanged.
- R2: `test_base_ci_never_calls_the_tracker_without_a_source`, one case for each source, and
  `test_base_ci_without_a_base_branch_is_unknown`.
- R3: `test_base_ci_reuses_the_cache_for_the_same_tip`, `test_an_old_or_future_cache_is_read_again`.
- R6: `test_a_raising_tracker_reads_as_unknown`.
- R4: `test_status_names_a_red_base`, `test_status_is_silent_on_green_pending_and_unknown`,
  `test_vet_strict_never_sees_ci`.
- R5: `test_status_with_a_fresh_cache_calls_nothing`, `test_the_tracker_is_given_ci_timeout`.
- R7: `tests/test_preflight.py::test_preflight_reports_ci_and_never_refuses_on_it`.
- R8: `test_ship_question_names_a_red_base`, `test_ship_question_command_reads_ci_itself`.
- R9: `tests/test_land.py::test_a_red_base_is_a_signal` (the signal, and `land-check`'s `clear`
  turning false), `test_an_unknown_base_is_no_signal` (unknown, pending, green).
- The copy: `test_core_reads_failures_by_the_trackers_words` pins `CI_FAILED` to `CI_RED`.
- R10: acceptance checks in `checks.md`.

## Rollback

`git revert` undoes everything in the repo. It doesn't remove `sdlc-ci.json`, which `status` and
`preflight` leave in each repo's git common dir. Nothing reads it once reverted, and
`rm "$(git rev-parse --git-common-dir)/sdlc-ci.json"` removes it. Nothing is published.
