---
id: 109
slug: landing-stops-only-for-cause
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 109 — A landing stops only for what needs the person · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`:
  - `cmd_land()`: the commit moves into `_land_commit()`; a `CalledProcessError` reports git's
    stderr/stdout tail (R7); a new branch before `_amend_record()` resumes a commit that failed
    after ship (R8), keeping `_amend_record()` for a hand-shipped `HEAD` (R9).
  - `land_parts()`: full note text from a new `note_items()` (R11), a proposal matched on full
    text or first line, an unproposed seed titled by `first_sentence()` (R12); `land_message()`
    calls `first_sentence()` instead of its own split.
  - `cmd_resolve(cont=True)`: when `INBOX` conflicted, `drop_entries()` the ids of a new
    `frontmatter_ids()` (`idea:`, `fixes:`) plus `named_nits()`, before staging; `dropped` in the
    output (R13). `retire_nits()` becomes a call to `drop_entries()`.
  - `loop_state()`: `approver` (new `decision_preamble()`) and `verifier` (`read_verified()`'s
    problems for the last round) join `mendable` (R10).
  - `land_verdict()`: a `mendable` block for round `land-<n>` (behaviour evidence, a verdict after
    a preamble, the verifier's problems), less the roles `land_mended()` lists; `next: mend` when
    every problem is mendable (R1, R2, R3, R6, R10).
  - `cmd_agent()` / `_task()` / `_land_task()`: `mend` refused unless `verdicts` names that role
    (R5); `mend` for `approver` and `verifier` (R10); new task `land-mend` in `TASKS` and
    `LAND_TASKS`, refused unless `land_verdict()` names that role, writing under
    `reviews/land-<n>/`, recorded `<role> land-<n>` (R3, R4); `verdict_mend()` widened to the
    approver and verifier and to a landing round; `--role` accepts `approver` and `verifier`;
    `VERIFY_MEND` and `DECISION_MEND` prompts; `WAYS["mend"]`'s sentence; `read_verified()`
    takes the file's name for its problems, so a landing round's say `reviews/land-<n>/`.
  - Docstrings of `cmd_verdicts()` and `cmd_land_verdicts()`.
- `plugins/factory/agents/reviewer-behaviour.md`, `approver.md`, `verifier.md`: one line each
  (every `$` gets its `exit:`; nothing before `DECISION:`; plain answer lines).
- `plugins/factory/skills/land/SKILL.md`: `next: mend` runs `agent --task land-mend --role <role>`
  per role, then `land-verdicts` again (R14).
- `plugins/factory/skills/build/SKILL.md`: the mend step names the approver and the verifier.
- `plugins/factory/README.md`, `AGENTS.md` (the factory paragraph): the widened mend.
- `tests/test_land.py`: the landing tests named by R1–R4, R6–R9, R11–R14.
- `tests/test_factory.py`: R5, R10's tests; two existing tests that mended a builder whose report
  had its evidence now give it a report without, since `mend` is refused otherwise (R5).

Reused, not re-derived: `read_evidence()`, `preamble()`, `read_verified()`, `mended()`'s file,
`named_nits()`, `_section()`, `FENCE_RE`, `_sdlc()`, `land_message()`, `land_round()`.

## Work order

1. **R7–R9: the landing commit.** `_land_commit()`, its error tail, the resume branch. Tests in
   `test_land.py` with a `commit-msg` hook.
2. **R11–R12: carried notes.** `note_items()`, `first_sentence()`, `land_parts()`.
3. **R13: the register after a resolution.** `frontmatter_ids()`, `drop_entries()`, `cmd_resolve`.
4. **R5: a build mend only when `verdicts` names it.** Refusal in `cmd_agent()`; existing tests
   adjusted.
5. **R10 in the build loop.** `decision_preamble()`, verifier problems in `mendable`, the mend
   tasks for approver and verifier.
6. **R1–R4, R6, R10 in a landing.** `land_mended()`, `land_verdict()`'s mendable block, the
   `land-mend` task.
7. **R14 and the words.** Skills, agent prompts, README, AGENTS.md, docstrings.

## Tests

- R1 `test_a_landing_review_missing_an_exit_is_mended_not_stopped`
- R2 `test_a_landing_verdict_after_a_preamble_is_mended`
- R3 `test_a_landing_mend_is_once_a_role_a_round`
- R4 `test_a_landing_mend_writes_into_its_landing_round`
- R5 `test_a_build_mend_is_refused_when_verdicts_names_none` (test_factory.py)
- R6 `test_a_landing_stops_for_cause_even_beside_a_mendable_problem`
- R7 `test_a_failed_landing_commit_carries_git_s_error`
- R8 `test_a_landing_whose_commit_failed_commits_on_rerun`
- R9 `test_a_hand_shipped_change_is_not_committed_again`: the old
  `test_a_record_is_never_amended_into_a_commit_the_landing_didnt_make`, renamed, its hand commit
  now holding `intent.md` at `stage: shipped`, since R8 reads one without it as a failed commit
- R10 `test_an_approver_s_preamble_is_mended_by_the_approver`,
  `test_a_verifier_s_unread_answers_are_mended_once` (test_factory.py), and the verifier in a
  landing inside R3's test
- R11 `test_a_carried_note_keeps_its_continuation_lines`
- R12 `test_an_unproposed_seed_is_titled_from_its_first_sentence`
- R13 `test_a_landing_resolution_never_keeps_the_change_s_own_seeds`,
  `test_a_landing_resolution_never_keeps_the_nits_it_retired`
- R14 `test_the_land_skill_names_its_mend`; `tests/test_skills.py` covers its rule.

## Rollback

`git revert` undoes all of it: nothing is written outside the repo, and no data format changes
(`runs/mended` gains `<role> land-<n>` lines, which the old `mended()` already skips).
