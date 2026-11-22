---
id: 230
slug: nit-flow
kind: plan
created: 2026-11-22
updated: 2026-11-22
---

# 230 — Nits are filed once, only while still true, and can be retired · plan

> Written by the factory's builder after reading the code: `agent_findings()`, `run_state`'s
> `handed`, `_task()`'s review prompt, `_inbox_commit()` and the factory's `Nits taken in:` reader.

## Files to change

- `plugins/factory/scripts/factory.py`: in `agent_findings()`, the decision order the spec's
  Design gives (a `later` round of the role means not filed: `fixed` with `FIXED_REASON`, or
  `minor` with `REPEAT_REASON` when a later nit names the same `LEAD_RE` path; then `low` value
  is `minor` with `LOW_REASON`); `HANDED_REASON` retired, `FIXED_REASON`, `REPEAT_REASON` (a
  `.format(round=…)` template) and `LOW_REASON` added; `reworked_round()` removed, since its only
  caller goes; in `_task()`'s review branch, the role's earlier nits (`earlier_nits()`, new,
  beside `agent_findings()`) through the new `earlier` part; `PROMPT_PARTS["review"]` gains
  `earlier: "before nits"`; docstrings of `agent_findings()` and `cmd_carry()`.
- `plugins/factory/prompts/review.md`: the new `## earlier` part.
- `scripts/sdlc.py`: `RETIRE_REASONS["nit"] = ("duplicate", "stale", "wontfix")` and its comment;
  core's copy of the factory's reader (`NIT_SECTIONS`, `TAKEN_RE`, `LIST_ITEM_RE`,
  `taken_lines()`, and `_section()` as `_nit_section()`, since core already has a `_section()`
  of another shape), with `nits_taken_in(folder, ids)`; `_nit_claims(home)` and the nit check in
  `_inbox_commit()` in place of the blanket refusal; `cmd_inbox_commit()`'s docstring.
- `skills/idea/SKILL.md`: Step 2's *Retire* bullet, the description, *Out of scope*.
- `docs/REFERENCE.md`: the register paragraph's "A nit … is never retired this way".
- `plugins/factory/README.md`: the nit paragraph (R1, R2, R5).
- Tests: `tests/test_factory_loop.py` (R1–R6: new tests, `test_a_nit_not_raised_again_is_still_filed`
  replaced, the three weight-dependent tests reweighed, the handed review prompt test extended
  for R4); `tests/test_prompts.py` and `tests/prompts/review-earlier.txt` (new case: a round-2
  review with earlier nits); `tests/test_bugs.py` (R7, R8); `tests/test_land.py` (R9's agreement
  test beside the factory reader's forms test); `tests/test_skills.py` (R10).

## Work order

1. **Filing (R1, R2, R3, R5, R6).** Red: the new `agent_findings`/`carry` tests in
   `test_factory_loop.py`, and the reweighed existing ones. Green: the decision order in
   `agent_findings()`, the reasons, `reworked_round()` gone.
2. **Asking again (R4).** Red: `test_a_review_names_its_roles_earlier_nits` and the new prompt
   case. Green: `earlier_nits()`, the `earlier` part, the prompt file, the recorded copy.
3. **Core's reader (R9).** Red: the agreement test. Green: the copy in `sdlc.py`.
4. **Retiring (R7, R8).** Red: the edited and new `test_bugs.py` tests. Green: the reasons,
   `_nit_claims()`, the check in `_inbox_commit()`.
5. **The skill and docs (R10, R11).** Red: `test_idea_retires_a_nit`. Green: `SKILL.md`, then
   REFERENCE.md, the factory README and the comments.

## Tests

- R1: `test_a_nit_a_later_round_raises_reworded_is_filed_once`.
- R2: `test_a_nit_no_later_round_raises_is_fixed_whatever_its_weights` (replaces
  `test_a_nit_not_raised_again_is_still_filed`).
- R3: `test_a_nit_not_filed_says_why`.
- R4: `test_a_review_names_its_roles_earlier_nits`; the `review-earlier` recorded prompt.
- R5: `test_the_factory_files_no_low_value_nit`; reweighed `test_carry_disposes_each_nit_by_its_weights`,
  `test_carry_caps_the_nits_it_files_at_five`.
- R6: `test_a_landing_round_never_changes_the_nits_filed`, reweighed.
- R7: `test_inbox_commit_retires_by_the_entry_s_kind`, edited.
- R8: `test_inbox_commit_never_retires_a_nit_an_open_change_takes_in`.
- R9: `test_core_reads_nits_taken_in_as_the_factory_does`.
- R10: `test_idea_retires_a_nit`.
- R11: by the review (docs); R12: the existing suite (`landing.py`, `guide/`, `defaults/` untouched).

## Rollback

`git revert` undoes all of it: no data is written outside the repo, no config key or trailer is
added. A nit retired through `/sdlc:idea` after this lands is a `Retire <id>` commit on the base
branch, which a revert of this change leaves; `git revert` of that commit restores the entry.
