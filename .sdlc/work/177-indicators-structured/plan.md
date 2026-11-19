---
id: 177
slug: indicators-structured
kind: plan
created: 2026-11-19
updated: 2026-11-19
---

# 177 — The retrospective reads indicators as rows and shows them as a table · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/indicators.py`: `HEADER`, `cell()` (escape `\` and `|`), `number()` (a value as the
  report writes it), `signed()` (a change as `+3` / `−2`), `host_rows()` (R1, R2's line reasons),
  `report_rows()` (R4's read-back, R8). Pure: `json` and `math` only.
- `scripts/retro.py`: `_indicator_rows(home, since, ran)` (R2's run reasons, R3, R4);
  `_architecture()`'s `host` through it; `_indicators_text()` (R5, R6); `render_report()` gains
  `indicators=None`; `retro_report()` runs `retro.indicators` alone through `_evidence()` (R7).
  Reuses `_evidence()`, `_table()`'s layout, `report_rel()`, `sdlc.last_retrospective()`,
  `sdlc._git()`.
- `scripts/sdlc.py`: `TEMPLATE_READS["retro.md"]` adds `Indicators` and `{{indicators}}` (R9).
- `templates/retro.md`: `## Indicators` / `{{indicators}}` after `## Spend`; the note names the
  host's `retro.indicators`.
- `.sdlc/setup.json`: re-recorded with `sdlc.py record` (R12).
- `.sdlc/function-heat.py`: `render()` → `rows()`, JSON Lines (R10).
- `skills/setup/drafts.md`: Step 2 **Indicators** item, Step 3 config bullet (R11).
- `docs/REFERENCE.md` (*Retrospectives*, *After an update*), `skills/retro/SKILL.md` (`host`),
  `AGENTS.md` (*Retrospectives*) (R12).
- `tests/test_indicators.py`: R1, R2 (line reasons), R8.
- `tests/test_retro.py`: R2 (run reasons), R3, R4, R5, R6, R7 (split assertion), R9.
- `tests/test_function_heat.py`: R10.
- `tests/test_skills.py`: `READS_CONFIG["sdlc:setup"]` gains `retro.indicators` (R11).

## Work order

1. **Rows from text and back** (`indicators.py`): `host_rows`, the formatters, `report_rows`,
   tested alone with a hand-built table and the formatters' own output.
2. **Rows in `retro`'s JSON** (`_indicator_rows`, `_architecture`): R2's run reasons, R3, R4 with
   a scratch repo holding a `Retrospective` commit whose report has a table.
3. **The report** (`_indicators_text`, template, `render_report`, `retro_report`,
   `TEMPLATE_READS`, `record`): R5–R7, R9, then the round trip R8 through `render_report`.
4. **`function-heat.py`** prints rows (R10).
5. **Setup** offers the key (R11).
6. **Docs** (R12).

## Tests

- R1: `test_indicator_rows_are_read_from_json_lines` (test_indicators.py).
- R2: `test_output_that_isnt_rows_passes_through_with_its_reason` (test_indicators.py, each line
  reason), `test_a_failed_or_cut_indicator_passes_through_with_its_reason` (test_retro.py, exit,
  timeout, truncation); `test_the_hosts_indicators_run_without_a_product_doc` unchanged.
- R3: `test_indicator_rows_reach_the_architecture_block`.
- R4: `test_an_indicator_is_compared_with_the_last_retrospectives_report`.
- R5: `test_the_report_renders_indicator_rows_as_a_table`.
- R6: `test_the_report_says_no_indicators_set`.
- R7: `test_retro_and_its_report_show_the_same_figures`, split.
- R8: `test_indicator_rows_round_trip_through_the_report`.
- R9: `test_the_report_renders_spend`, extended (the old override misses both sections).
- R10: `tests/test_function_heat.py`, rows parsed with `json.loads`, and the output for this
  repo's files under `EVIDENCE_LIMIT`.
- R11: `test_skills_read_host_specifics_from_config[sdlc:setup]`.
- R12: the drift test in the gate (`sdlc.py drift` clean after `record`).

## Rollback

`git revert` undoes all of it. Nothing is written outside the repo. A `Retrospective` commit
made after this change holds a report with the `## Indicators` table; after a revert it is
history, read by nothing.
