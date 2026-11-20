# 191 — Pay down the open tests nits · plan

> How the change is built: the files it touches, the order of the work, the test each nit gets,
> and what a revert wouldn't undo. Tier 1, written because the Approach reaches across fourteen
> test files.

## Files to change

Tests only; no script, doc or default changes.

- `tests/uv_run.py` (new, not a test module, imported like `train_driver.py`): `uv_script()`,
  `UNREACHED` and `UNCACHED`, moved from `test_adoption.py`'s `_uv()`.
- `tests/test_adoption.py`: imports `uv_script as _uv`; tests of the fallback itself.
- `tests/test_train.py`: `by()` goes through `uv_script()`; the kill tests share one bound;
  stop rows, the stop's failing append, a stop before any move, the R9 read-only edit.
- `tests/test_land.py`: `ALREADY`/`MADE` hoisted and renamed.
- `tests/test_retro.py`, `test_board.py`, `test_prompts.py`, `test_registry.py`,
  `test_modules.py`, `test_evals.py`, `test_sdlc.py`, `test_comment_health.py`,
  `test_feature_map.py`, `test_archive.py`: one nit each, or a few.

Reused: `drive_train()`, `_three()`, `_begin()`, `_folder()`, `factory.land_round()`,
`_doctored()`, `_factory()`, `_retro()`, `health.measure()`.

## Work order

One test file at a time, each nit's test run by name and seen failing against a deliberately
broken copy of the code before it was put back (the checks below say which):

1. `test_evals`, `test_sdlc`, `test_registry` (red: `main()` binding `status` at import).
2. `test_board`, `test_modules` (red: a `LAND_STOPS` entry the factory never writes).
3. `test_prompts` (red: `land-mend` naming only `mend.md`).
4. `test_retro`.
5. `test_train`: the stop and R9 assertions, the shared kill bound.
6. `tests/uv_run.py`, then `test_adoption` and `test_train`'s `by()` on it (red: no fallback,
   and the old one-wording match).
7. `test_land`, `test_comment_health` (red: no shebang rule), `test_feature_map`,
   `test_archive`.

## Tests

| Nit | Test | Proves |
|---|---|---|
| 2026-11-18-79 | none | answered in `notes.md`: the call takes about 3 s now |
| 2026-11-18-101 | `test_only_the_evals_own_workspace_is_removed` | `outside`'s modes restored in `finally` |
| 2026-11-18-104 | `test_the_source_guards_reach_closing_py` | docstring names where the other two plants are |
| 2026-11-18-109 | `test_main_runs_a_stand_in_handler` | no command reaches `cli_status` through globals, without `--all` |
| 2026-11-19-6 | `test_the_stops_status_reads_are_the_ones_the_factory_writes` | `LAND_STOPS` pinned to the factory's `_record_land()` calls |
| 2026-11-19-7 | `test_modules.py` helpers | each has a docstring |
| 2026-11-19-8 | `test_land_mend_is_refused_on_either_of_its_files` | both of `land-mend`'s files refuse it |
| 2026-11-19-11 | `_bare_repo` | docstring: conftest's `git_identity` gives its author |
| 2026-11-19-17 | `test_retro_and_its_report_show_the_same_figures`, `test_the_report_shows_the_value_figures_in_its_window` | follow-through's sentence matches the JSON |
| 2026-11-19-20 | `test_retro_autonomy_rates_kept_defaults_without_the_landings_yes` | the rate's denominator is kept + changed |
| 2026-11-19-23 | the kill tests | one bound, `STARTED_WITHIN`, with its reason |
| 2026-11-19-29 | none | answered in `notes.md` |
| 2026-11-19-38 | `test_an_ejection_is_recorded_and_amended_in` | a stop row's `land` and `at` |
| 2026-11-19-40 | `test_an_indicator_that_cannot_start_is_a_failure_not_rows` | an OSError is `failed: could not start` |
| 2026-11-19-49 | `test_land.py`, `test_train.py` | the constants hoisted, renamed apart |
| 2026-11-19-51 | `test_a_line_one_shebang_is_not_a_comment` | a line-1 `#!` isn't counted |
| 2026-11-19-55 | `test_a_stop_that_cant_be_recorded_still_stops` | the stop's failing append |
| 2026-11-19-56 | `test_a_change_with_no_start_leaves_its_commits_unknown` | the `unknown` row's `change` |
| 2026-11-19-57 | `test_a_stop_before_any_change_moved_leaves_no_row` | the edge case |
| 2026-11-19-67 | `test_the_pillar_sections_show_autonomy_pipeline_and_cost` | the landing line's own label |
| 2026-11-19-73 | `test_the_loop_rechecks_before_it_runs_accept` | a read-only edit still loses clearance |
| 2026-11-19-75, -78 | `test_a_close_that_hands_off_runs_under_the_parents_hold` | `by()` is `uv_script()` |
| 2026-11-19-76 | `test_an_uncached_script_skips_however_uv_words_it` | four wordings skip; a script's failure doesn't |
| 2026-11-19-77 | `test_an_unreached_index_runs_the_script_again_from_the_cache` | the fallback, with uv stood in |
| 2026-11-20-2 | `test_no_doc_uses_a_retired_phrasing` | one phrasing a line |
| 2026-11-20-4 | `east` | `try`/`finally`, and why it is never `portable` |

## Rollback

Nothing outside `tests/` and the change folder: `git revert` undoes all of it.
