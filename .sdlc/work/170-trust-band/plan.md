---
id: 170
slug: trust-band
kind: plan
created: 2026-11-19
updated: 2026-11-19
---

# 170 — The retrospective says how far its numbers can be trusted · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/metrics.py`: `read_events()`'s three loops (the main session's, `_run()`'s, and
  `_subagent()`'s through `_run()`) note each distinct `version` and `message.model` (not empty,
  not `<synthetic>`) and emit one `runtime{claude?, model?}` per distinct value per run, at the
  value's first timestamp. A new helper, `_runtime(entries)`, is shared by the main loop and
  `_run()`. `summarize()` skips `runtime` as it skips `mode`, so a runtime event's timestamp can't
  stretch a stage's end. New pure `runtime_trailer(events, role_models, plugin)` sits beside
  `lead_trailer()`. The docstring's contract names both.
- `scripts/closing.py`: `finish()` builds the line inside its own `try`, after the lead line,
  from `events`, `_agent_models()`' values and `sdlc.plugin_version()`. On a raise it adds
  ` runtime=failed` to coverage and leaves the line out. `_lead_marks()`' first mark (events[0])
  skips `runtime` events, so lead time is the same as before.
- `scripts/retro.py`:
  - `_coverage(changes, measured, why)` returns `{coverage: {measured, of, greyed}, missing_because}`.
    It has four callers: `lead_view()` (`_lead_why()`), `metrics_summary()` (`_minutes_why()`),
    `_spend()` (its `recorded` and `why`) and `process_views()` (escapes, all of the window).
  - `_none_reason(coverage)`: the `none:` text without the ` key=value` words close appends
    (` lead=failed`, ` runtime=failed`). `_unrecorded()` uses it too, so spend's `why` stops
    carrying those words.
  - `underneath(changes, previous)` (pure) and `_previous_window(home, trunk, since)`, which reuses
    `sdlc.retrospectives()` and `sdlc.closed_changes()`. `process_views()` gains an optional
    `previous` argument and stores `process.underneath`.
  - `process_views()` counts `window.factory` and `window.mode_unknown`, and sets
    `landing_catches` to None when `factory` is 0.
  - `render_report()` gains an optional `metrics` argument. `_window_text()` appends the
    coverage lines and the underneath line to `{{window}}`. `_sources_text()` says
    `No factory changes in this window.` in place of the catches line.
  - `retro()` and `retro_report()` pass the previous window and `metrics_summary()` through.
- `tests/test_metrics.py`: R1 and R2 tests.
- `tests/test_archive.py`: R3's failure test and the line on a normal close.
- `tests/test_adoption.py`: R3's `^Sdlc-Runtime: plugin=\d+\.\d+\.\d+$` assertion.
- `tests/test_retro.py`: R4–R12 tests.
- `docs/REFERENCE.md` (*Metrics*, *Retrospectives*) and `docs/RETRO-SCORECARD.md` (S11's two
  figures): R13.
- `skills/retro/SKILL.md`: one bullet beside `unmeasured` (R14).

Reused, not re-derived: `_word()`, `_model_word()` and `_word_text()` for sanitising,
`parse_trailers()` unchanged (`Sdlc-Runtime` falls to `out[key] = fields`), `_agent_models()`,
`sdlc.plugin_version()`, `sdlc.retrospectives()` and `sdlc.closed_changes()` (as `bugs_retro()`
already uses them), and `_unrecorded()`'s reading of `none:`.

One departure from the spec's wording (R2): each version is passed through `_model_word()`, not
`_word()`. `_word()` keeps `,` and `:`. A `,` inside one value would split it when the values are
joined, and `a:1` reads back through `_value()` as a dict. `_model_word()` is `_word()` with those
two characters also replaced, so the line is still free of `/`, `~` and spaces.

Departures found while building:

- **The skills' cases in a host's `prose` (R11).** The spec assumed nothing in retro mentions the
  cases. In fact `prose_metrics()` lists every side file of each skill, ship's `cases.md`
  included, so a host's JSON named it. `OWN_REPO_BRANCHES` leaves that branch out of a host's
  `prose` (its size and its commands), since `SHIP_BRANCHES` names it only where `_cases_report()`
  finds the suite. `test_prose_counts_each_of_the_plugins_skills` now checks both sides.
- **`landing_catches` gated on `Sdlc-Mode` (R10).** 136's
  `test_retro_counts_a_landing_catch_once_per_change` built factory-reviewed changes with no
  `Sdlc-Mode`. Its fixture now carries the `Sdlc-Mode: factory` that every real factory close
  writes.
- **Tests pinning the old shapes.** These were updated:
  - 162's `test_close_times_a_factory_change_from_its_run_files`: `Sdlc-Lead` is no longer the
    last measured line;
  - `test_the_process_views_count_cycle_throughput_time_and_load`: `escapes` and `window` gain
    keys;
  - `test_without_a_lead_line_every_other_figure_is_as_it_was`: `lead` gains `coverage`.
- **`_lead_marks()`' first mark** skips `runtime` events, and `summarize()` skips them too, so
  no existing figure moves.

## Work order

1. **Runtime events (R1).** `test_runtime_is_read_from_each_entrys_version_and_model` goes red,
   then `_runtime()` and the three loops. `summarize()` skips the kind. The existing metrics
   tests stay green.
2. **The trailer (R2).** `test_runtime_trailer_round_trips` goes red, then `runtime_trailer()`.
3. **Close writes it (R3).** First the adoption assertion and
   `test_a_failed_runtime_read_never_stops_a_close`, then `finish()` and `_lead_marks()`.
4. **Coverage (R4–R6).** The coverage tests go red, then `_coverage()` and its four callers.
5. **Report coverage lines (R7).** `test_the_report_greys_a_thin_headline`, then
   `_window_text()` and the `metrics` argument.
6. **Underneath (R8, R9, R12).** The underneath tests, then `underneath()`,
   `_previous_window()`, wiring, and the report line.
7. **No factory changes (R10).** The test, then the counts and the sentence.
8. **Hosts never see the cases (R11).** A test only: nothing mentions the cases today. It fails if
   the change adds a mention.
9. **Docs and skill (R13, R14).**

## Tests

- R1: `tests/test_metrics.py::test_runtime_is_read_from_each_entrys_version_and_model`.
- R2: `tests/test_metrics.py::test_runtime_trailer_round_trips`.
- R3:
  - `tests/test_archive.py::test_a_failed_runtime_read_never_stops_a_close`;
  - `tests/test_archive.py::test_close_writes_the_runtime_line`;
  - `tests/test_archive.py::test_a_drop_records_the_plugin_alone`;
  - `tests/test_adoption.py`'s new `Sdlc-Runtime` assertion.
- R4, R5: `tests/test_retro.py::test_every_headline_says_its_coverage_and_why_the_rest_is_missing`.
- R6: `tests/test_retro.py::test_a_headline_under_half_its_changes_is_greyed`.
- R7: `tests/test_retro.py::test_the_report_greys_a_thin_headline`.
- R8: `tests/test_retro.py::test_what_changed_underneath_compares_with_the_last_window` and
  `test_the_last_window_runs_from_the_start_with_one_retrospective`.
- R9: `tests/test_retro.py::test_the_report_says_what_changed_underneath`.
- R10: `tests/test_retro.py::test_a_window_with_no_factory_changes_says_so`.
- R11: `tests/test_retro.py::test_a_hosts_retrospective_never_mentions_the_cases`, with
  `test_prose_counts_each_of_the_plugins_skills` for the own repo's side.
- R12: `tests/test_retro.py::test_underneath_reads_history_alone`.
- R13, R14: read by the review. `tests/test_skills.py` and the gate stay green.

## Rollback

`git revert` undoes all of it. What it doesn't undo: the `Sdlc-Runtime` lines and the
` runtime=failed` words that closes write in the meantime stay in history. Both are harmless after
a revert: `parse_trailers()` reads an unknown key into its own slot, and no reader counts it.
Nothing is published, and nothing is written outside the repo.
