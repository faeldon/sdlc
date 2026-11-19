The retrospective now compares factory-built changes with hand-built ones on lead time, throughput, cost and escape rate. Throughput is also split by work class. A retired grouped seed reads `dropped`, and the setup-record nit is fixed. The full gate passed (3307 tests), and nothing is committed.

## Slices built
1. **R12, setup's record:** `_is_process()` no longer skips `.sdlc/setup.json`. The docstring and REFERENCE.md now say it counts like any other `.sdlc/` path.
2. **R9–R11, retired seeds:**
   - New `sdlc.retired_entries(home, trunk, since=None)` gives each retired entry's id, and its title as the register held it just before the `Retire` commit. `retro.py`'s `_retired_ids()` is removed and `_seed_follow()` reads the new function.
   - `_milestone_verdicts()` gives a grouped seed `dropped` when a `Retire` matched it by id or by title. It only walks the log when a grouped seed has left the register.
   - `_milestone_follow()`: a milestone whose rows are all closed, shipped or dropped is `done` if any row was built, and `dropped` if none was.
   - `status` counts `dropped` as finished, so every milestone it called done before is still done.
3. **R1, R2, lead by way:** `WAYS` and `_way()` read the way from `Sdlc-Mode` alone. `process.lead` gains `ways`, and its per-tier groups use `_way()`.
4. **R3, R4, throughput:** each week's row gains `ways` and `classes`, with every key present. `retro_report()` now classes the changes before it counts the weeks. The throughput table gains *Ways* and *Classes* columns.
5. **R7, escapes:** each escape row gains `way`, and `bugs.rate.window` gains `by_way`.
6. **R5, R6, `by_way()`:** a pure function that both `retro()` and `retro_report()` call. `_cost()` hands over its landed changes under `_landed`, and both callers remove that key before showing `cost`. Cost compares in tokens for both ways, with dollars where recorded.
7. **R8, the report:** `_by_way_text()` adds the *By way of building* table at the end of `{{window}}`, after the value sentences. No template changed.
8. **R13, docs:** REFERENCE.md (*Retrospectives* and the direction-doc paragraph), RETRO-SCORECARD.md (throughput, the escape-rate guardrail and cost marked captured, S9 done in wave 3) and `skills/retro/SKILL.md` (`by_way`, `dropped` in `direction.milestones` and in step 5).

## Tests added (each seen failing first, for the expected reason)
| Requirement | Test |
|---|---|
| R1 | `test_a_change_with_no_sdlc_mode_counts_as_unknown_way` |
| R2 | `test_lead_time_is_given_by_way_across_tiers` |
| R3 | `test_throughput_counts_each_week_by_way_and_by_work_class` |
| R4 | `test_the_report_s_throughput_shows_work_classes` |
| R5 | `test_by_way_gives_every_figure_for_each_way_with_its_n` |
| R6 | `test_hand_built_cost_compares_in_tokens_and_is_missing_in_dollars` |
| R7 | `test_escape_rate_is_split_by_the_introducing_change_s_way` |
| R8 | `test_the_report_compares_the_ways_of_building` |
| R9, R10 | `test_a_grouped_seed_retired_by_inbox_commit_reads_dropped` (also checks `_retired_ids` is gone) |
| R11 | `test_a_milestone_whose_grouped_seeds_were_retired_follows_through_as_dropped`, and `test_status_counts_a_milestone_with_a_retired_seed_done` in `test_next_up.py` |
| R12 | `test_a_change_touching_only_setup_s_record_is_process_work` |

`test_follow_through_scores_the_last_retrospective_s_seeds` passes unchanged, as R10 requires. Five existing tests pinned the exact old shapes, so I extended their assertions for the new keys only:
- `test_retro.py`: the process-views throughput assertion and the no-lead-line `lead` dict.
- `test_bugs.py`: the escape row's `way`, the empty `rate.window`, and the parametrised rate test.

The first gate run failed on 7 of those `test_bugs.py` cases (shown below) before I made that change.

## Plan and notes
- `plan.md` is written. The build follows it.
- `notes.md` has one unticked item:
  - `by_way.throughput` floors the window at one day, as R5 says. On this repo today that gives `weeks: 0.1`, which inflates the per-week figures (196 factory changes a week).
- A live `sdlc.py retro` on this repo shows all three ways in every part of `by_way`. The last throughput week's `ways` and `classes` both sum to its total of 29. `manual.cost.usd` is n 0 with `built by hand`, and `manual.cost.tokens.n` is 1.

- DECISION: [default] Keep R5's "at least 1/7 week" floor for `by_way.throughput`, as specified. Going ahead with it unless told otherwise.
  - OPTION: keep the one-day floor — matches the spec; a retro run just after the last one shows inflated per-week figures
  - OPTION: floor at one week — calmer figures early in a window; understates throughput in a short window
  - OPTION: `per_week` null under a week — never misleads; no figure until a week has passed
  - WHY: the spec's R5 sets the floor at 1/7, and changing it is the person's call

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_retro.py -k setup_s_record   (before the fix)
1 failed, 206 deselected in 1.85s
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py -k "retired"   (before the code)
2 failed, 1 passed, 206 deselected in 1.39s
exit: 1

$ uv run --group dev pytest -q tests/test_next_up.py -k retired_seed   (before the code)
E       AssertionError: assert ['closed', 'vanished'] == ['closed', 'dropped']
1 failed, 33 deselected in 0.17s
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py -k "unknown_way or every_figure_for_each or hand_built_cost"   (before by_way)
3 failed, 213 deselected in 2.79s
exit: 1

$ uv run --group dev pytest -q -n 4 tests/test_retro.py tests/test_next_up.py tests/test_modules.py tests/test_feature_map.py
284 passed in 30.17s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 176   (first run)
FAILED tests/test_bugs.py::test_the_escape_rate_moves_against_the_window_before[5-5-1-3-up] (and 4 more of it)
FAILED tests/test_bugs.py::test_retro_counts_bugs_reported_fixed_retired_open_and_escaped
FAILED tests/test_bugs.py::test_retro_counts_no_bugs_as_nothing
7 failed, 3300 passed, 29 skipped in 197.43s (0:03:17)
exit: 1

$ uv run --group dev pytest -q -n 4 tests/test_bugs.py
58 passed in 6.64s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 176
All checks passed!
314 files already formatted
3307 passed, 29 skipped in 166.01s (0:02:46)
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q -n 4 tests/test_retro.py tests/test_next_up.py tests/test_bugs.py -k "setup_s_record or retired or follows_through_as_dropped or given_by_way_across or throughput_counts or throughput_shows or split_by_the_introducing or unknown_way or every_figure_for_each or hand_built_cost or compares_the_ways or scores_the_last_retrospective_s_seeds"
15 passed in 3.09s
exit: 0

$ uv run --quiet --script scripts/sdlc.py retro | python3 -c '…print by_way and the last throughput row…'
{"changes": {"factory": 28, "manual": 1, "unknown": 0}, … "cost": {… "manual": {"tokens": {"n": 1, "median": 991590, "missing_because": {}}, "usd": {"n": 0, "median": null, "missing_because": {"built by hand": 1}}} …}, "escapes": {"factory": {"escapes": 4, "changes": 28, "rate": 0.14}, "manual": {"escapes": 1, "changes": 1, "rate": 1.0}, …}}
{'week': '2026-11-16', 'tiers': {'1': 9, '2': 20}, 'total': 29, 'ways': {'factory': 28, 'manual': 1, 'unknown': 0}, 'classes': {'fix': 4, 'capability': 10, 'process': 2, 'debt': 13, 'unclassed': 0}} 29 29
exit: 0
