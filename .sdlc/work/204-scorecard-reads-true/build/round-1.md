All three of the intent's outcomes are built and tested, and the full gate passes (3545 passed, 29 skipped, exit 0). Nothing is committed. The change is in `scripts/retro.py`, `tests/test_retro.py`, `tests/test_surface.py` and `docs/REFERENCE.md`, plus `plan.md` and `notes.md` in the change folder.

## Slices built

1. **The workarounds' `unknown` block now has its `n`** (seed 2026-11-20-15). It is built the same way as `outside` and `hand_record`: it has `n`, its count is null rather than 0 when `n` is 0, and it has a `missing_because`.
2. **The lead-time-by-way rows say `no <way> change in the window`** when the window closed no change of that way (seed 2026-11-20-24, nit 2026-11-20-25). That is the escape rate's reason, and both now come from one helper, `_no_way()`. The coverage-greyed hint still shows.
3. **The surface counts a key as used when its readers ran** (seed 2026-11-20-39):
   - A new `_code_reads()` walks the code of the core's scripts and trackers. For each `sdlc.py` command it follows everything the command calls, `load_config()` included, and finds the config keys read by name: directly, through `.get`, through a local name bound to a section, through a section passed into a function, and inside methods. A key that is only written doesn't count.
   - `_key_readers()` adds the skills whose files name a key as `section.key`.
   - A key is **used** when the config sets it or any reader of it ran in the window.
   - It is **unused** when a reader that the records could show didn't run, or nothing reads it.
   - Otherwise it is **unmeasured**: `no change recorded it`, or `read only where no record shows it`. That second reason never makes a retire candidate.
   - `git.base` and `git.push` are now read by every command that loads the config, so they drop off the retire list.

## Tests added
- `test_a_change_with_no_start_leaves_its_commits_unknown` and `test_every_null_scorecard_row_names_its_reason`: `unknown` has an `n`, and in a window with no commit its count is null with a reason.
- `test_a_figure_with_no_data_reads_a_dash_with_its_reason`: the factory lead row now reads `no factory change in the window`, the same as the escape row. Its old expectation, `none in the window`, is the behaviour the seed asked to change.
- `test_the_scan_follows_what_a_command_reads_by_name`: each kind of read is found from sample code, and a key that is only written is not.
- `test_git_base_and_push_are_read_by_the_commands_that_load_the_config`: `ship` and `status` read `git.base` and `git.push`, `close` reads `metrics.idle_minutes` through a section passed into a function, and skills read the keys they name.
- `test_every_key_has_a_reader`: every config key has some reader, so a key the scan misses can't show up as a false retire candidate.
- `test_a_key_is_used_when_a_reader_of_it_ran`: covers used, unused and both unmeasured reasons.
- `test_a_key_its_readers_use_is_never_a_retire_candidate`: a key nothing reads is retired after three windows; `git.base`, `git.push` and a key only outside commands read are not.
- `test_a_key_is_used_when_the_config_sets_it`: now uses a made-up key to show that a default alone is no setting.

## Changes to `plan.md` and what's in `notes.md`
- **`plan.md`:** the factory's scripts aren't scanned. They read no config key by name, and scanning them would widen what the core reads of the factory beyond the command names it already reads.
- **`notes.md`:** explains why the scan over-counts. A function counts as reached whenever its name is mentioned, so about 30 of the 46 keys count as read by most commands. One unticked item: follow only real calls if the surface should tell keys read on every run apart from keys read on one branch.

- DECISION: [default] Should a key count as read when any function a command can reach reads it, even on a branch that doesn't run? Going ahead with this unless told otherwise.
  - OPTION: anything reachable — it errs towards `used`, which is the safe side for a retire list, and it covers the intent's "every key load_config() reads"; but most keys read as used by most commands
  - OPTION: only keys read on every run — closer to "on every run", but it needs flow analysis that a static scan can only approximate
  - WHY: the retire list must keep only keys nothing read, and a missed read would show a key the code still reads as a retire candidate
- DECISION: [default] Should a skill that names a key in its files count as reading it? Going ahead with yes.
  - OPTION: yes — `commands.build`, `build_when`, `close_list`, `worktree_setup` and `docs.review` are read only by skills (ship, close, intent, spec), through `config`'s output
  - OPTION: commands only, as the Approach says — those five keys would wrongly become retire candidates
  - WHY: the outcome says "the retire list keeps only keys nothing read"

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_surface.py
5 failed, 17 passed in 10.15s
exit: 1

(the red run, before the scan existed)

$ uv run --group dev pytest -q tests/test_retro.py::test_a_change_with_no_start_leaves_its_commits_unknown tests/test_retro.py::test_every_null_scorecard_row_names_its_reason
2 failed in 4.01s
exit: 1

(red, before `unknown` had its `n`)

$ uv run --group dev pytest -q tests/test_retro.py::test_a_figure_with_no_data_reads_a_dash_with_its_reason
E       AssertionError: assert 'none in the window' == 'no factory c...in the window'
1 failed in 0.84s
exit: 1

(red, before the lead rows gave the way's reason)

$ uv run --group dev pytest -q -n auto tests/test_surface.py tests/test_retro.py tests/test_modules.py tests/test_windows.py tests/test_feature_map.py
389 passed in 51.60s
exit: 0

$ uv run --group dev pytest -q tests/test_surface.py tests/test_retro.py::test_a_change_with_no_start_leaves_its_commits_unknown tests/test_retro.py::test_every_null_scorecard_row_names_its_reason tests/test_retro.py::test_a_figure_with_no_data_reads_a_dash_with_its_reason
25 passed in 26.29s
exit: 0

$ uv run --group dev ruff check scripts tests && uv run --group dev ruff format --check .
All checks passed!
326 files already formatted
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 204
All checks passed!
3545 passed, 29 skipped in 239.14s (0:03:59)
✔ Validation passed
exit: 0
