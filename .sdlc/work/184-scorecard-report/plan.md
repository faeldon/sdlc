---
id: 184
slug: scorecard-report
kind: plan
created: 2026-11-19
updated: 2026-11-19
---

# 184 — The retrospective report opens with the scorecard · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/retro.py`:
  - `report_figures()` (new) takes over the shared half of `retro()` and `retro_report()`: the
    per-change loop (bases, paths, `days_open`, `release`, so `value_band()` reads it rather than
    asking again), `_rework`, `bugs_retro`, `value_band`, `process_views`, `metrics_summary`,
    `_cost` (its one call site), `by_way`, `_autonomy`, `_pipeline`, `_workarounds`, `_spend`,
    `surface()` when asked, and `scorecard()`. `retro()` keeps its own size fields, the product
    pass, architecture, prose, tests and register. `retro_report()` adds `_indicator_rows()` and
    renders.
  - `scorecard()` (new, pure) builds the rows from the blocks (R3–R7). `_row_note()` and
    `_trend()` are its helpers. `SCORECARD_HEAD` is the table's header.
  - `_last_rows()` returns both tables' rows from the last report: the indicator rows as now, and
    the scorecard's `(pillar, figure)` value and `n`, through the generalised `report_rows()`.
  - `render_report()` takes the new blocks as keyword arguments. It adds `scorecard`, `speed`,
    `quality`, `autonomy`, `cost`, `simplicity`, and keeps `{{window}}` as today when the template
    has no `{{scorecard}}`. The new renderers are `_scorecard_text()`, `_pipeline_speed_text()`,
    `_pipeline_quality_text()`, `_autonomy_text()`, `_cost_text()` and `_simplicity_text()`.
  - `by_way()`: `per_week` is null and `why` reads `window under a week` under 7 days (R13).
  - `_pipeline()`: `per_change` on `bisections` and `accept_stops` (R18).
  - `bugs_retro()`: each distinct `Introduced by:` is resolved to its change once, memoised in a
    dict that both the escapes loop and the rate read (R19).
  - `_surface_at()` gets a comment, and `_retire()` a docstring sentence (R16, R17).
- `scripts/indicators.py`: `report_rows(text, head=INDICATOR_HEAD, keys=(0, 1), value=2)`.
  `host_rows()` rejects a `—` unit and stray spaces (R15).
- `scripts/sdlc.py`: `TEMPLATE_READS["retro.md"]` gains `Scorecard` and `{{scorecard}}` (R11).
- `templates/retro.md`: the new layout (R1).
- `skills/retro/SKILL.md`: Step 0 names `scorecard`; Step 2's process pass reads
  `simplicity.workarounds` (R14).
- `docs/REFERENCE.md` (*Retrospectives*, *After an update*), `docs/RETRO-SCORECARD.md` (R20).
- `.sdlc/setup.json` via `sdlc.py record` (R21).
- Tests: `tests/test_retro.py`, `tests/test_indicators.py`, `tests/test_surface.py`,
  `tests/test_skills.py` (or `test_retro.py` for R14's check).

- `.sdlc/work/184-scorecard-report/checks.md` (new): R17's and R20's doc sentences.

**Where the build departed from the plan:**

- `render_report()` takes the table as `card=`, not `scorecard=`: `scorecard` is the function, and
  `values` already keys the section `scorecard`.
- `report_figures()`'s `surface` flag shadows the `surface()` function inside it, so the module
  binds `_surface = surface` and `report_figures()` calls that.
- R14's test lives in `tests/test_retro.py` (`test_the_retro_skill_s_process_pass_reads_workarounds`).
- Two older tests changed with R1 and R2: `test_no_figure_folds_speed_and_stability_into_one` now
  looks for `score` as a word, because the `Scorecard` heading holds the letters. The window tests
  (`..._value_figures_in_its_window`, `..._greys_a_thin_headline`,
  `..._what_changed_underneath`, `..._compares_the_ways_of_building`) now read the Value band
  and Trust band from `## Scorecard` and the by-way table from `## Speed`.
  `..._renders_indicator_rows_as_a_table` checks for `band` only in `## Indicators`, since the
  template's note now says "Value band".
- The template's note names "the scorecard's table" rather than the `## Scorecard` heading. A
  heading's text in the note is where `split("## Indicators")` cut the template first.

## Work order

1. **The nits and seeds, which stand alone:** R15 (`host_rows`), R16/R17 (surface comment and
   docstring), R18 (`per_change`), R13 (`by_way` under a week), R19 (`bugs_retro` memo). Each one
   test first.
2. **One computation:** `report_figures()`, with `retro()` and `retro_report()` on it. Then the R12
   counting test. The existing suite in `test_retro.py` pins that nothing moved.
3. **`report_rows()` generalised** in `indicators.py`. Its existing tests pin the indicator path.
4. **`scorecard()`** with its rows, notes, last and trend (R3, R5, R6, R7), in the JSON (R4).
5. **The template and `render_report()`:** the scorecard, the pillar sections, and the old
   `{{window}}` for an override without `{{scorecard}}` (R1, R2, R8, R9, R10). Then
   `TEMPLATE_READS` (R11), with the two old slicing tests moved to the new order.
6. **Skill, docs, record** (R14, R20, R21).

## Tests

- R1: `test_the_report_s_sections_come_in_order` checks the headings' order and that no `{{` is
  left. The shape is pinned by `test_defaults.py`.
- R2: `test_the_scorecard_holds_the_value_band_table_and_trust_band_once`.
- R3: `test_scorecard_rows_for_a_host_and_for_the_plugin` (pure, on constructed blocks).
- R4: `test_the_report_s_table_reads_back_as_the_json_s_rows`.
- R5: `test_a_figure_with_no_data_reads_a_dash_with_its_reason`.
- R6: `test_a_greyed_lead_time_is_marked_a_hint`.
- R7: `test_a_second_retrospective_carries_the_first_s_values_as_last`,
  `test_a_first_scorecard_has_no_last_and_no_trend`, and `test_a_row_under_five_gets_no_trend`.
- R8: `test_the_pillar_sections_show_autonomy_pipeline_and_cost`.
- R9: `test_a_host_s_simplicity_shows_workarounds_alone` and
  `test_the_plugin_s_simplicity_shows_its_surface`.
- R10: `test_an_override_from_before_still_renders_every_placeholder`.
- R11: `test_an_override_without_the_scorecard_is_breaking`, plus the two updated slicing tests.
- R12: `test_report_figures_runs_cost_once` (a counting stand-in, plus a source check that `_cost(`
  is called only inside `report_figures`).
- R13: `test_by_way_throughput_is_null_under_a_week`, plus the existing 3-week assertion with
  `why: None`.
- R14: `test_the_retro_skill_s_process_pass_reads_workarounds`.
- R15: `test_host_rows_refuse_a_dash_unit_and_stray_spaces` (parametrised).
- R16: `test_a_tag_before_the_registry_has_no_commands`.
- R17: the existing `windows == 2` pin.
- R18: `test_bisections_and_accept_stops_carry_per_change`.
- R19: `test_introducers_are_resolved_once_whatever_the_bugs`.
- R20: the review, and the Verification `grep`.
- R21: the gate's `drift` check.

## Rollback

`git revert` undoes all of it. Nothing is written outside the repo. A host's committed reports from
before stay as they are, and reports written by this version stay readable by an older one, whose
`report_rows()` reads the indicator table by its own header alone. `.sdlc/setup.json` is reverted
with the rest.
