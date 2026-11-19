---
id: 176
slug: by-way-of-building
kind: plan
created: 2026-11-19
updated: 2026-11-19
---

# 176 — The retrospective compares factory-built changes with hand-built ones · plan

> Written by the builder after reading `scripts/retro.py`, `scripts/sdlc.py`'s
> `_milestone_verdicts()` and `next_up()`, and `tests/test_retro.py` / `tests/test_next_up.py`.

## Files to change

- `scripts/retro.py`: `WAYS`, `_way()`; `lead_view()` gains `ways`; `process_views()`'s
  throughput rows gain `ways` and `classes`; `_cost()` returns its landed `(rec, usd)` list under
  `_landed`; `bugs_retro()` gives each escape its `way` and `rate.window.by_way`; new pure
  `by_way()`; `retro()` and `retro_report()` build it (the report classes before it counts);
  `_by_way_text()` and the throughput table's two columns in `render_report()`; `_retired_ids()`
  removed, `_seed_follow()` reads `sdlc.retired_entries()`; `_milestone_follow()`'s dropped rule;
  `_is_process()` stops skipping `sdlc.MANIFEST`.
- `scripts/sdlc.py`: new `retired_entries(home, trunk, since=None)`; `_milestone_verdicts()` gives
  a retired grouped seed `dropped`; `next_up()`'s done check takes `dropped`.
- `tests/test_retro.py`: the named tests of R1–R12.
- `tests/test_next_up.py`: `test_status_counts_a_milestone_with_a_retired_seed_done` (R11).
- `docs/REFERENCE.md` (*Retrospectives*), `docs/RETRO-SCORECARD.md`, `skills/retro/SKILL.md`: R13.

Reused, never re-derived: `_p85()`, `_coverage()`, `_minutes_measured()`/`_minutes_why()`,
`_cost_why()`, `_share()`, `_table()`, `sdlc.parse_entries()`, `sdlc.ref_matches()`,
`sdlc.names_change()`, `sdlc._git()`.

## Work order

1. **R12, setup's record.** Test a setup-only change classes `process`; drop the skip; docstring.
2. **R10, R9, R11, retired seeds.** `retired_entries()` with the existing seed follow-through
   test still green; `_milestone_verdicts()`'s `dropped`; `_milestone_follow()`'s rule; `status`'s
   tuple. Tests for each, the status one in `test_next_up.py`.
3. **R1, R2, lead by way.** `_way()`, `lead_view()`'s `ways`.
4. **R3, R4, throughput by way and class.** The week counters; `retro_report()` calls
   `value_band()` before `process_views()`.
5. **R7, escapes by way.** Row `way`, `rate.window.by_way`.
6. **R5, R6, `by_way()`.** `_cost()`'s `_landed`, popped by both callers; tokens from totals.
7. **R8, the report.** `_by_way_text()` after the value sentences; throughput's columns.
8. **R13, docs.**

Each slice ends with its own tests run by name.

## Tests

- R1: `test_a_change_with_no_sdlc_mode_counts_as_unknown_way`
- R2: `test_lead_time_is_given_by_way_across_tiers`
- R3: `test_throughput_counts_each_week_by_way_and_by_work_class`
- R4: `test_the_report_s_throughput_shows_work_classes`
- R5: `test_by_way_gives_every_figure_for_each_way_with_its_n`
- R6: `test_hand_built_cost_compares_in_tokens_and_is_missing_in_dollars`
- R7: `test_escape_rate_is_split_by_the_introducing_change_s_way`
- R8: `test_the_report_compares_the_ways_of_building`
- R9: `test_a_grouped_seed_retired_by_inbox_commit_reads_dropped`
- R10: `test_follow_through_scores_the_last_retrospective_s_seeds` (unchanged), and the removal of
  `_retired_ids` checked by R9's test reaching `sdlc.retired_entries`.
- R11: `test_a_milestone_whose_grouped_seeds_were_retired_follows_through_as_dropped`,
  `test_status_counts_a_milestone_with_a_retired_seed_done`
- R12: `test_a_change_touching_only_setup_s_record_is_process_work`
- R13: review and grep; the gate.

## Rollback

`git revert` undoes all of it: the change writes no data, no trailer and nothing outside the repo.
Retrospective reports already committed keep the figures they were written with.
