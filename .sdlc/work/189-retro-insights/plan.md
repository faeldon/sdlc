---
id: 189
slug: retro-insights
kind: plan
created: 2026-11-20
updated: 2026-11-20
---

# 189 — The retrospective's report answers its own questions: the Insights section · plan

> Written after reading `scripts/retro.py` (`render_report()`, `scorecard()`, `report_figures()`,
> `retro()`, `cmd_retro()`, `cmd_retro_commit()`, the blocks R11 names), `scripts/sdlc.py`'s
> `GUIDES`, `CONFIG_KEYS`, `DOC_FILES`, `doc_path()`, `doc_units()` and `TEMPLATE_READS`, the retro
> skill, the core agents and their tests.

## Files to change

- `scripts/retro.py`: `_trend()`, `_minutes()` (R12, R13); `render_report()` takes `figures`
  whole and `insights` (R10, R7); `missing_because` on the four blocks (R11); new
  `INSIGHT_PILLARS`, `INSIGHT_FIELDS`, `INSIGHT_KINDS`, `INSIGHT_DATA`, `NOT_ANSWERED`,
  `insights_rel()`, `insight_questions()`, `insight_bundles()`, `insight_answers()`,
  `_insights_text()`; `cmd_retro(..., insights=)`; `retro_report(..., insights=)` reads the draft;
  `cmd_retro_commit()` reads, checks and removes the draft (R2–R7).
- `scripts/sdlc.py`: `GUIDES["insights"]`, `CONFIG_KEYS["docs"]["insights"]`, `DOC_FILES` and
  `cmd_config()`'s optional list gain `insights`; `retro --insights` flag; `retro-commit`'s help.
- `guide/insights.md` (new): the seven questions (R1).
- `agents/insight.md` (new): `sdlc:insight` (R5).
- `templates/retro.md`: `## Insights` / `{{insights}}` after `## Scorecard`, the note (R8).
- `skills/retro/SKILL.md`, `skills/retro/insights.md` (new): `Agent`, the side file, Step 4–6 (R9).
- `tests/test_retro.py`: the new tests, `SECTIONS` gains Insights, render_report calls (R10).
- `tests/test_skills.py`: the agent test, the spawn test, `SHIP_AGENTS`-set in
  `test_sdlc_loads_nothing_from_plugins` gains `insight`, retro's `allowed-tools` list.
- `tests/test_sdlc.py` or `test_retro.py`: config reports `docs.insights` (R2).
- `docs/REFERENCE.md`, `AGENTS.md`, `docs/FEATURES.md`, `docs/PROCESS.md` (R14).
- `.sdlc/setup.json`: rerecorded, the template's hash and the new key (R14).

Reused, not re-derived: `sdlc.doc_units()` for both question docs, `sdlc.parse_entries()` for the
register's ids, `_coverage()` / `_minutes_measured()` / `_minutes_why()` for the response reasons,
`indicators._parsed()` for the trend's read-back, `sdlc._lean()` and `cmd_retro()`'s leaning for the
bundles.

## Work order

1. **Nits (R12, R13).** `_trend()` compares `_parsed(_num(value))`; `_minutes()` rounds to one
   place. Tests first.
2. **`render_report(template, figures, *, indicators, insights)` (R10).** Mechanical; existing
   calls move to `{"process": process}`; `retro_report()` passes `f`.
3. **Null reasons (R11).** `missing_because` on the four blocks; scorecard passes each to `add()`.
4. **The guide and the host doc (R1, R2).** `guide/insights.md`, the config key,
   `insight_questions()`.
5. **`retro --insights` (R3, R4).** Bundles from `retro()` run with the three host-command lists
   emptied; JSON out.
6. **The agent (R5).** `agents/insight.md` and its test.
7. **Draft, commit and template (R6, R7, R8).** `insight_answers()`, `_insights_text()`, the
   template's section, `retro_report()` reading the draft, `cmd_retro_commit()`'s refusals,
   commit and removal.
8. **The skill (R9).** `Agent`, `insights.md`, Steps 4–6.
9. **Docs and record (R14).**

## Departures from the spec, as built

- **The response reasons live in `process.response`, not `time.tiers[t]`.** `time` is None when no
  change was measured, which is exactly the window R11's test builds, so a reason kept there
  could never be read. `process.response` holds `_coverage()` per tier over every change of that
  tier, always present; the scorecard's response rows read it (decision raised as a default).
- **R12 changes nothing a test can see.** `number()` writes `str(value)`, which `float()` reads back
  exactly, so `_trend()` already compared what the table shows; the nit's premise doesn't hold.
  `_trend()` now compares `_parsed(_num(value))` as the spec asks, and the test pins it (it passed
  on the old code too).
- **`test_prose_counts_each_of_the_plugins_skills`** assumed retro had no side file; it now
  expects `insights.md` as retro's one branch.
- **`retro --report` previews the draft** through `_draft_answers()`, shared with `retro-commit`;
  `retro_report()` takes the answers explicitly.

## Tests

- R1 `test_the_insights_guide_asks_one_question_per_pillar`; `tests/test_defaults.py` globs it.
- R2 `test_a_host_insights_doc_replaces_adds_and_places`; `test_config_reports_the_insights_doc`.
- R3 `test_each_insight_gets_only_its_pillars_figures`.
- R4 `test_retro_insights_runs_no_host_command`.
- R5 `test_the_insight_agent_reads_and_returns_the_shape`; `test_sdlc_loads_nothing_from_plugins`.
- R6 `test_retro_commit_refuses_an_insight_missing_a_field`,
  `test_retro_commit_refuses_a_seed_the_register_lacks`,
  `test_retro_commit_renders_the_insights_and_removes_the_draft`.
- R7 `test_the_insights_say_not_answered_without_a_draft`.
- R8 `test_an_override_without_insights_still_renders`,
  `test_insights_is_not_a_template_read`; `test_the_report_s_sections_come_in_order`.
- R9 `test_the_retro_insights_file_spawns_its_agent`; the WAIT and side-file tests.
- R10 `test_render_report_takes_the_figures_whole`.
- R11 `test_every_null_scorecard_row_names_its_reason`.
- R12 `test_a_trend_reads_flat_against_its_own_written_value`.
- R13 `test_minutes_keep_one_decimal`.
- R14 `tests/test_feature_map.py`; `sdlc.py drift` empty after `record`.

## Rollback

`git revert` undoes all of it. Nothing outside the repo is written. A host that ran a
retrospective with this version has an `## Insights` section in a committed report, which stays
as history; the next retrospective after a revert reads back only the scorecard table, so nothing
is misread. A leftover `.sdlc/retros/<date>.insights.md` draft (only if a person stopped between
Step 6's write and `retro-commit`) would show as untracked: `rm` it.
