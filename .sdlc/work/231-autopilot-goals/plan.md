---
id: 231
slug: autopilot-goals
kind: plan
created: 2026-11-22
updated: 2026-11-22
---

# 231 — Autopilot runs toward a goal, and plans the seeds it takes to reach it · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `direction_open(home, cfg)` (new), the direction doc's open goals and
  milestones, each milestone's grouped seeds resolved to open register ids with `ref_matches()`
  over `inbox_entries()`, and `direction_items()`'s `problems`; `cli_status --json` prints it as
  `direction` beside `next_up` (R1). Reuses `direction_items()`, `_direction_text()`,
  `inbox_entries()`, `is_nit()`, `ref_matches()`.
- `plugins/factory/scripts/autopilot.py`:
  - `status_read()` (new) returns items, direction and why; `status_items()` stays its two-value
    wrapper (the existing tests and the loop read it).
  - `resolve_goal()`, `goal_scope()`, `propose_goal()` (new, pure): R2–R4.
  - `candidates(…, goal=None)`: one filter on `goal["scope"]` (R3).
  - `preview()`: `--goal` resolved or a goal proposed; `goal`, `alternatives`, the question and
    `shown`'s `Goal:` block (R5).
  - `begin_refusals()` / `cmd_autopilot(goal=…)`: the goal refusals; `state["goal"]` and
    `state["register"]` (R6, R11).
  - `register_ids()` (new) over `factory.INBOX` with `factory.ENTRY_RE` and `factory.FENCE_RE`.
  - `wave_brief()`: `## Goal` and `Level:` (R7, R12).
  - `read_plan()` replaces `read_wave()`; `WAVE_RE` takes tier and reason, `NONE_RE` goes (R8).
  - `plan_wave()` / `open_wave()` / `apply_wave()`: the plan kept in `state["plans"]`, each LEAVE in
    `state["seeds"]` with `left` (R9); `open_seed()` gets the WAVE line and writes `Planned:` into
    the intent brief (R10).
  - `summary()` / `write_summary()` / `end_run()`: `goal`, `plans`, `register`, and the sections
    `## Goal`, `## The plan`, `## Left for you`, the register's counts under `## The run` (R11, R12).
- `plugins/factory/scripts/factory.py`: `cli_autopilot` gains `--goal` and passes it.
- `plugins/factory/prompts/autopilot.md`: the `wave` part asks for R8's format (one line).
- `plugins/factory/agents/autopilot-planner.md`: R8's format, the goal, reading the code to leave
  a seed already fixed or wrong; no `NONE`, no "rank order alone".
- `plugins/factory/skills/autopilot/SKILL.md`: Step 1 asks for a goal; `--goal` passed; Step 2's
  quoted question; Step 3 passes `goal.arg`; the description names the goal (R13).
- `plugins/factory/README.md`: *Autopilot* names the goal, its three sources, the plan and the
  report's register line (R13).
- `docs/FEATURES.md`: the autopilot line says it runs toward a goal.
- `tests/prompts/autopilot-wave.txt`: the recorded `wave` prompt, re-recorded
  (`SDLC_RECORD_PROMPTS=1`) from the new prompt part.
- Tests: `tests/test_autopilot.py` (new and extended tests, the `Steps` stand-in writing plan
  replies that place every candidate), `tests/test_sdlc.py` untouched (R1's test is in
  `test_autopilot.py`, through the real `sdlc.py`, as the spec names).

## Work order

1. **R1, the direction through `status --json`.** `test_goals_come_from_the_real_status_json`
   red, then `direction_open()` and the `--json` print.
2. **R2, R3, the goal and its scope.** `test_a_goal_is_read_by_its_form`,
   `test_a_goal_only_narrows_the_candidates` red; `resolve_goal()`, `goal_scope()`, the filter in
   `candidates()`.
3. **R4, R5, the preview.** `test_the_preview_proposes_a_goal_when_none_is_stated`, the extended
   `test_autopilot_preview_writes_nothing`; `propose_goal()`, `preview()`'s question and `shown`.
4. **R6, R11's start, `--begin`.** The new refusal cases, the extended
   `test_autopilot_begin_writes_the_state_once`; `--goal` on the CLI, `register_ids()`.
5. **R7, R8, the plan.** `test_the_wave_brief_names_the_goal`,
   `test_the_planner_places_every_candidate`, the extended
   `test_planner_reply_is_checked_by_the_script`; `wave_brief()`, `read_plan()`; the loop tests'
   replies move to the plan format (a `Steps` helper builds a plan placing each candidate).
6. **R9, R10, what a plan does.** `test_a_seed_the_planner_leaves_is_left_for_the_person`,
   `test_the_intent_brief_carries_the_plan`, the end-to-end byte checks; `apply_wave()`,
   `open_seed()`.
7. **R11, R12, the report and an old state.** `test_the_summary_says_whether_the_register_grew`,
   `test_a_run_begun_without_a_goal_resumes`; `summary()`, `write_summary()`.
8. **R13, the words.** `test_the_skill_quotes_the_preview_question`; the skill, the prompt part,
   the planner, the README, FEATURES.md.

## Tests

- R1: `test_goals_come_from_the_real_status_json`.
- R2: `test_a_goal_is_read_by_its_form`.
- R3: `test_a_goal_only_narrows_the_candidates`.
- R4: `test_the_preview_proposes_a_goal_when_none_is_stated`.
- R5: `test_autopilot_preview_writes_nothing` (extended), and
  `test_the_preview_names_a_goal_from_the_direction_doc` (a milestone proposed, a `--goal` the doc
  doesn't hold open refused, the doc's problems and a goal with no candidate as warnings).
- R6: `test_autopilot_begin_refusals` (`no goal`, `a closed milestone`),
  `test_autopilot_begin_writes_the_state_once` (extended).
- R7: `test_the_wave_brief_names_the_goal`.
- R8: `test_planner_reply_is_checked_by_the_script` (extended), `test_the_planner_places_every_candidate`.
- R9: `test_a_seed_the_planner_leaves_is_left_for_the_person`, `test_autopilot_end_to_end` (bytes).
- R10: `test_the_intent_brief_carries_the_plan`.
- R11: `test_the_summary_says_whether_the_register_grew`; `test_summary_names_every_call_and_no_machine` still.
- R12: `test_a_run_begun_without_a_goal_resumes`.
- R13: `test_the_skill_quotes_the_preview_question`; `tests/test_skills.py` unchanged.

## Rollback

`git revert` of the change's commit undoes all of it: nothing is published and no data format a
host keeps changes. A run's state written by this version holds `goal`, `register` and `plans`,
which the older code ignores (it reads keys by name), so a run begun under this change resumes
under the reverted code, planning as before. A planner reply already filed in a run's folder is a
report, read by nothing after the wave it answered.
