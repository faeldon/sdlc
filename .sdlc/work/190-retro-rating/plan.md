---
id: 190
slug: retro-rating
kind: plan
created: 2026-11-20
updated: 2026-11-20
---

# 190 — The retrospective asks how working with the process felt · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/retro.py`: beside the insights code (`insights_rel()`, `_draft_answers()`,
  `_insights_text()`), add `experience_rel()`, `EXPERIENCE_HEAD`, `EXPERIENCE_FIGURE`,
  `EXPERIENCE_LABELS`, `NOT_RATED`, `NO_LINE`, `experience_answer()`, `_draft_experience()`,
  `_experience_trend()`, `_experience_text()`, `_last_experience()`. Extend `_last_rows()` with
  `experience` (`_last_experience()`, reusing `indicators.report_rows()` for the table), `render_report()` with `experience=`,
  `retro_report()` to pass it and the last rating through, `cmd_retro(--report)` to preview a
  draft, `cmd_retro_commit()` to read, refuse, render and remove the draft exactly as the
  insights draft is handled, and `retro()`'s output with `experience: {last}` from the
  `_last_rows()` call `report_figures()` already makes (kept in `figures["experience_last"]`).
- `templates/retro.md`: `## Experience` / `{{experience}}` after `## Insights`; the note says so.
- `skills/retro/SKILL.md`: Step 0 names `experience` and, for R14, keeps `work_mix`,
  `time_to_users`, `follow_through`; Step 2's Direction pass weighs the last rating; Step 5's
  dialog asks the rating second; Step 6 writes `.sdlc/retros/<today>.experience.md`; Step 7 says
  whether a rating was recorded.
- `docs/REFERENCE.md` *Retrospectives*: an *Experience* paragraph; `{{experience}}` among the
  optional placeholders.
- `docs/PROCESS.md`: the retro `writes:` node names the experience draft.
- `AGENTS.md` *Retrospectives*: one clause naming the experience draft beside the insights one.
- `.sdlc/setup.json`: rewritten by `sdlc.py record` after the template edit.
- Tests: `tests/test_retro.py` (R4–R10, R14; `test_render_report_takes_the_figures_whole`'s
  signature pin gains `experience`), `tests/test_skills.py` (R1–R3, R12),
  `tests/test_metrics.py` (R11), REFERENCE phrase test in `tests/test_retro.py` (R13).

## Work order

1. **The parser.** `experience_answer()` and its parametrized test (R4). Pure, nothing depends
   on anything else.
2. **The section, rendered.** `_experience_text()`, `_experience_trend()`, the template's section,
   `render_report(experience=…)`, `retro_report()`; `NOT_RATED` with no draft from `retro_report`
   and `retro --report` (R6), `SECTIONS` updated, the override test (R10), not a template read.
3. **The commit.** `_draft_experience()`, `cmd_retro_commit()` handling: render, refuse a draft
   with no `Answer:` (R7), remove after commit (R5), leave on a failed commit (R8).
4. **Read back.** `_last_rows()`'s `experience`, the row's last and trend, and `retro()`'s
   `experience.last` (R9).
5. **Metrics pin.** The two-question dialog test (R11), no code.
6. **Skill.** Step 0/2/5/6/7 edits and the two skills tests (R1–R3, R12), plus R14's docs test.
7. **Docs.** REFERENCE, PROCESS.md, AGENTS.md (R13), then `sdlc.py record` (R15).

## Tests

- R1–R3: `test_the_retro_wait_asks_the_rating_second_in_its_dialog` (`tests/test_skills.py`),
  with the existing WAIT tests still green.
- R4: `test_an_experience_answer_reads_its_rating_and_line` (parametrized).
- R5: `test_retro_commit_renders_the_rating_and_removes_its_draft`.
- R6: `test_the_experience_says_not_rated_without_a_draft`.
- R7: `test_retro_commit_refuses_an_experience_draft_without_an_answer`.
- R8: `test_a_failed_commit_leaves_the_experience_draft_for_a_rerun`.
- R9: `test_the_next_retro_reads_the_last_rating_back`.
- R10: `test_experience_is_not_a_template_read`, `test_an_override_without_experience_still_renders`,
  `SECTIONS` gains `Experience` (`test_the_report_s_sections_come_in_order`,
  `test_an_override_without_insights_still_renders`).
- R11: `test_a_two_question_gate_reads_its_approval_from_the_first_answer` (`tests/test_metrics.py`).
- R12: `test_the_retro_skill_reads_the_last_rating`.
- R13: `test_reference_names_the_rating_and_its_draft`; `tests/test_feature_map.py`.
- R14: `test_reference_and_step_0_name_the_aim_keys`.
- R15: `sdlc.py drift` reports nothing; the gate fails otherwise.
- Manual, before ship (spec *Contracts touched*): read one real two-question retro transcript and
  confirm `toolUseResult.answers` lists the approval first.

## Rollback

`git revert` undoes all of it. Not covered: a host's committed reports that already hold an
`## Experience` section stay in history, harmless (a reverted reader ignores the table); an
experience draft left uncommitted in a host's `.sdlc/retros/` would then be a stray file
`retro-commit` refuses: delete it with `rm .sdlc/retros/<date>.experience.md`.
