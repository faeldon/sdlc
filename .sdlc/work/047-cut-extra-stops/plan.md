---
id: 047
slug: cut-extra-stops
kind: plan
created: 2026-11-10
updated: 2026-11-10
---

# 047 — Cut the stops a change makes between its gates · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/metrics.py`: `read_events` emits `harness` for task notices and compaction summaries,
  and marks a human event `command` for any slash command (`plugin` for the plugins' own),
  `asked` and `interrupt`; `summarize` counts `harness` and `command` per stage and never as
  stops, and gives each extra stop its kind in `close_span()`; `trailers()` writes `Sdlc-Extra`,
  and `harness=`/`command=` on `Sdlc-Totals`; `parse_trailers` reads it; docstring.
- `scripts/sdlc.py`: `metrics_summary()` gains `extra`, from `_extra_report()` beside
  `_prompt_report()`.
- `skills/spec/SKILL.md`: `EnterPlanMode` allowed; the WAIT names starting plan mode; Step 6
  calls it.
- `skills/intent/SKILL.md`: `EnterPlanMode` allowed; Tier 1's WAIT offers it (`yes, without plan
  mode`); Step 6 calls it on yes.
- `skills/retro/SKILL.md`: reads `extra` beside `prompts`.
- `docs/REFERENCE.md`: *Metrics* documents `Sdlc-Extra` and what is not a stop.
- `tests/test_metrics.py`, `tests/test_retro.py`, `tests/test_skills.py`: R1–R6, R9.
- `.sdlc/work/047-cut-extra-stops/spec.md`: R4/R5 name the `Sdlc-Totals` marker.

## Work order

1. `metrics.py` events, summary and trailers, with `tests/test_metrics.py` (R1–R5).
2. `sdlc.py`'s `_extra_report()`, with `tests/test_retro.py` (R6).
3. The spec, intent and retro skills, with `tests/test_skills.py` (R7–R9).
4. `docs/REFERENCE.md` and the docstring (R10); `./check.sh`.
5. The classifier's numbers for 041–046 rerun through the new code, against the spec's table.

## Tests

- R1: `test_harness_entries_are_not_the_person`: a task notice and a compaction summary add
  `harness=2`, no stop, and leave response and away as without them.
- R2: `test_another_slash_command_is_not_a_stop`: `/reload-plugins` is `command=1`, stops
  unchanged.
- R3: `test_each_extra_stop_has_its_kind`, and `test_no_text_leaves_a_human_event`.
- R4: `test_extra_kinds_round_trip_through_the_trailers`.
- R5, R6: retro over one old `Close` commit and one with `Sdlc-Extra`: `recorded == 1`, kinds from
  the new one only.
- R7–R9: skills test: `EnterPlanMode` in spec's and intent's `allowed-tools` and named after their
  WAIT, and each WAIT question says `plan mode`.
- R10: read at ship's context pass.

## Rollback

`git revert` of the change's commit covers everything here. `Close` commits written while it was
live keep their `Sdlc-Extra` lines and `harness=`/`command=` fields; after a revert they are read
as unknown keys, never an error, since `parse_trailers` keeps any key and retro ignores it.
