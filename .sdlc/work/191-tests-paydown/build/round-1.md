I built 191, and all 26 nits are dealt with: 20 got a test or a fix, and 6 are answered in `notes.md`. Everything is uncommitted, and only `tests/` and the change folder changed. The full gate passed (3450 passed, 29 skipped). Two `test_retro.py` assertions (-56, -67) were added while that gate was running, so the gate may not have seen them; I reran them by name afterwards and they pass.

One part of the intent's outcome had nothing to do: the kill tests have no long polls to drop. Each wait checks every 0.05 s and stops as soon as its marker file appears. The 20–27 s each test takes is the train's own landing. Both waits already used 120 s; they now share one named bound, `STARTED_WITHIN`, with its reason.

For each new test, I broke the code it guards on purpose and saw the test fail, then put the code back. In the table, "red" names what I broke.

**Slices built**
| Nit | What changed |
|---|---|
| 2026-11-19-75, -78 | New `tests/uv_run.py` (`uv_script()`, `UNREACHED`, `UNCACHED`), imported the way `train_driver.py` is. `test_adoption.py` and `test_train.py`'s `by()` both use it, so `by()` now falls back to uv's cache when offline. |
| 2026-11-19-76 | The skip now matches four ways uv words a missing cached dependency, not only "network was disabled". It also requires the `--offline` run to have failed. |
| 2026-11-19-77 | `test_an_unreached_index_runs_the_script_again_from_the_cache` and `test_an_uncached_script_skips_however_uv_words_it` (×4 wordings), with uv's subprocess call stood in. Red: no fallback, and only the old wording. |
| 2026-11-18-101 | The `outside` workspace's permissions are restored in a `finally`. |
| 2026-11-18-109 | `test_main_runs_a_stand_in_handler` now also covers running with no command: it reaches `cli_status` at run time, without `--all`. Red: `main()` binding `status` at import. |
| 2026-11-19-6 | New `test_the_stops_status_reads_are_the_ones_the_factory_writes` checks `LAND_STOPS` against the steps the factory actually records. Red: a stop the factory never writes. |
| 2026-11-19-7 | Docstrings on `test_modules.py`'s helpers. |
| 2026-11-19-8 | New `test_land_mend_is_refused_on_either_of_its_files` (×2). Red: `land-mend` naming only `mend.md`. |
| 2026-11-19-17 | Follow-through's report sentence is now compared with the JSON in both report tests. |
| 2026-11-19-20 | A second decisions ledger, heavy on confirmed and settled lines, pins the rate at 2 of 3. |
| 2026-11-19-40 | New `test_an_indicator_that_cannot_start_is_a_failure_not_rows`: a shell that can't start is `failed: could not start`. |
| 2026-11-19-56 | Asserts the `change` on each `unknown` row. |
| 2026-11-19-67 | Speed's figures are matched by their line labels, not as bare words. Red: a renamed label. |
| 2026-11-19-38 | A stop's row now has its `land` and `at` checked. |
| 2026-11-19-55 | New `test_a_stop_that_cant_be_recorded_still_stops`. |
| 2026-11-19-57 | New `test_a_stop_before_any_change_moved_leaves_no_row`. |
| 2026-11-19-73 | The R9 test adds an edit to `checks.md` that the read-only list passes; it still loses the clearance. |
| 2026-11-19-49 | `ALREADY`/`MADE` in `test_land.py` moved to the top and renamed `ALREADY_MADE`/`MADE_REPORT`; `test_train.py`'s copy is now `ALREADY_MADE_REPLY`. |
| 2026-11-19-51 | New `test_a_line_one_shebang_is_not_a_comment`. Red: no shebang rule. |
| 2026-11-20-2 | The phrasing fixture lists one phrasing per line. |
| 2026-11-20-4 | The `east` fixture restores the timezone in `try`/`finally`, and its docstring says why it is never marked `portable`. |

**Answered in `notes.md`**
- **2026-11-18-79:** the browser test's call takes about 3 s here; the 49 s was a loaded gate.
- **2026-11-19-23:** the shared bound above.
- **2026-11-19-29:** that `checks.md` belongs to a change that has already closed, so editing it changes nothing.
- **2026-11-18-104:** all four plants exist, next to the guards they test; the docstring now says where.
- **2026-11-19-11:** conftest's autouse `git_identity` already gives every test a git author.

**`plan.md`:** written for this Tier 1 change because it touches fourteen test files. It has the nit-by-nit test table and was kept in step as I built.

**Left in `notes.md`**
- [ ] The workarounds' `unknown` block has no `n`, though its docstring says every count carries one. That is a code fix, outside a tests-only change.
- [ ] The intent's open question (land after R5's split of `test_factory.py`?) can be struck: this change doesn't touch that file.

No decisions raised.

## Evidence

$ uv run --group dev pytest -q -n 4 tests/test_adoption.py tests/test_retro.py tests/test_board.py tests/test_prompts.py tests/test_registry.py tests/test_modules.py tests/test_evals.py tests/test_comment_health.py tests/test_feature_map.py tests/test_archive.py tests/test_board_browser.py tests/test_sdlc.py
1197 passed, 28 skipped in 212.23s (0:03:32)
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 191
All checks passed!
3450 passed, 29 skipped in 212.79s (0:03:32)
✔ Validation passed
exit: 0

$ uv run --group dev ruff check tests/ && uv run --group dev ruff format --check tests/
All checks passed!
96 files already formatted
exit: 0

$ uv run --group dev pytest -q -n 4 tests/test_retro.py tests/test_land.py tests/test_train.py -k "already_made or fix or hands_off or killed or stop or recorded_and_amended or rechecks or pillar or no_start or kept_defaults or cannot_start or same_figures or value_figures"
51 passed, 1 skipped in 124.33s (0:02:04)
exit: 0

$ uv run --group dev pytest -q tests/test_registry.py::test_main_runs_a_stand_in_handler   # with main() binding status at import
1 failed in 0.21s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py::test_the_stops_status_reads_are_the_ones_the_factory_writes   # with a LAND_STOPS entry the factory never writes
1 failed in 0.16s
exit: 1

$ uv run --group dev pytest -q tests/test_prompts.py -k land_mend_is_refused   # with land-mend naming only mend.md
1 failed, 1 passed, 61 deselected in 0.16s
exit: 1

$ uv run --group dev pytest -q tests/test_adoption.py -k "unreached_index_runs or uncached_script_skips"   # with no fallback and the old one-wording match
5 failed, 13 deselected in 0.24s
exit: 1

$ uv run --group dev pytest -q tests/test_comment_health.py -k shebang   # with the line-1 shebang rule removed
1 failed, 17 deselected in 0.04s
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py -k pillar_sections_show   # with "Bisections:" relabelled
1 failed, 236 deselected in 27.73s
exit: 1

$ uv run --group dev pytest -q tests/test_board_browser.py --durations=5
2.92s call     tests/test_board_browser.py::test_the_drawer_holds_focus_and_returns_it_to_its_card
2 passed in 9.22s
exit: 0

$ uv run --group dev pytest -q tests/test_train.py -k "killed" --durations=5
27.29s call     tests/test_train.py::test_a_train_run_killed_at_its_gate_resumes
20.93s call     tests/test_train.py::test_a_killed_train_run_resumes
2 passed, 1 skipped, 135 deselected in 48.26s
exit: 0
