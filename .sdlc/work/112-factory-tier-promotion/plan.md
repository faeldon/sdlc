---
id: 112
slug: factory-tier-promotion
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 112 — Promote a change to Tier 2 in the middle of a factory run · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `cmd_upgrade()` and its `upgrade` subparser (R1, R2). `new`'s template
  substitution moves into `render_template()`, which both call. `_stamp()` takes no `new_key`
  for a stamp that adds no key, so `upgrade` edits `tier:`, `stage:` and `updated:` by
  `stamp_shipped`'s rule. `FACTORY_UPGRADED_FILE_RE` (a pinned copy) and
  `factory_upgraded_build()`, which `check` asks beside `factory_first_build()` (R12).
- `plugins/factory/scripts/factory.py`:
  - `UPGRADED_RE`, `UPGRADED_FILE_RE` and `UPGRADE_ANSWER_RE`.
  - `upgrade_answer()` (R3) and `read_upgrade()` (the record, or why it won't read).
  - `newest_round()`, taken out of `restart_state()` so `upgrade` counts `P` the same way.
  - `_rounds_at_depth()` passes the upgrade round to `depth()`'s `starts` and returns `upgrade`.
  - `loop_state()`: `upgraded`, `upgrading` and `written`, the `upgrade` and `spec` steps, `build`
    at `P`, and `first` counted from the newer of the restart and the upgrade (R3, R5, R6).
  - `cmd_upgrade()` and its subparser (R4, R5).
  - `_task()`: the spec prompt, the round-`P` build prompt, and the reviewer and approver lines
    (R7, R8, R10). `decided` refuses during an upgrade (R9).
  - `cmd_agent()`: the round-`P` build resumes the builder (R8).
  - `cmd_start()`'s `upgraded` and `cmd_fresh()`'s `held` (R11).
  - `PAUSES` and `_record_step()` (R13).
  - The module docstring and `cmd_verdicts()`'s.
- `scripts/board.py`: `PAUSES`, a pinned copy, read by `_progress()` (R13).
- `plugins/factory/skills/build/SKILL.md`: the `upgrade` rule, the decide note, and the
  `upgrade` and `spec` bullets. Step 2 gains the upgraded wording and Step 3 the stage moves owed
  (R14).
- `plugins/factory/agents/builder.md`: how a Tier 1 builder raises an upgrade (R15).
- `plugins/factory/README.md`, `AGENTS.md` (the factory paragraph) and `docs/REFERENCE.md` (the
  `sdlc.py upgrade` command) (R15).
- Tests:
  - `tests/test_sdlc.py`: R1, R2 and R12.
  - `tests/test_factory.py`: R3 to R11, R13's `AFTER:`, and the pinned record pattern.
  - `tests/test_board.py`: R13's track and the `PAUSES` pin.
  - `tests/test_skills.py`: R14's step coverage.

Reused, never re-derived:

- `template_path()`, `trunk_refusal()`, `names_change()`, `work_dir()` and `frontmatter_list()`
  in `sdlc.py`.
- `_sdlc()`, `read_ledger()`, `_scaffold()`, `set_stage()`'s rule, `build_round()`,
  `read_restarts()`'s shape, and `step_text()` in `factory.py`.

## Work order

1. **`sdlc.py upgrade`** (R1, R2). Tests first in `tests/test_sdlc.py`, on a scratch git repo on
   a change branch: tier, stage and date set by line, scaffolds only where missing, `check
   --strict` clean, and four refusals that write nothing. Then `render_template()` out of
   `cmd_new`, `cmd_upgrade()`, the subparser, and REFERENCE.md's line.
2. **The answer and the record** (R3, R4, R5). Tests in `tests/test_factory.py`:
   - `verdicts` names `upgrade` only on a ticked, decided, blocking `upgrade to Tier 2…` answer.
   - `factory.py upgrade` writes the record and then runs `sdlc.py upgrade`. It moves no `HEAD`
     and finishes a run cut short.
   - No second upgrade.

   Then the regexes, `read_upgrade()`, `upgrade_answer()`, the `upgrade` branch, `cmd_upgrade()`
   and a bad record as a stop.
3. **Spec, then build at `P`** (R6, R7, R8, R9, R10). Tests:
   - `spec` while the stage isn't `build`, with `written`, then `build` at `P`.
   - The limit, `exhausted` and the depth counted from `P`.
   - The spec prompt, and the round-`P` build resuming the builder.
   - `decided` refused.
   - The reviewer and approver prompts.

   Then `loop_state()`'s branches, `depth()`'s starts, `_task()` and `cmd_agent()`.
4. **`start` and `fresh`** (R11). Tests, then `upgraded` in `start` and `held` in `fresh`.
5. **`check` during the live round-`P` build** (R12). Tests beside 105's, then the pinned pattern
   and `factory_upgraded_build()`.
6. **The paused step** (R13). Tests for `AFTER:` on `upgrade` and `spec`, the board's track and
   its pinned `PAUSES`. Then `_record_step()` and `_progress()`.
7. **The skill and the docs** (R14, R15). The step-coverage test first, then the skill, the
   builder's definition, the README, the docstrings, AGENTS.md and REFERENCE.md. Run the gate.

## Tests

- **R1:** `test_upgrade_sets_tier_and_stage_by_line`,
  `test_upgrade_scaffolds_only_what_is_missing` and `test_upgrade_leaves_check_strict_clean`, in
  `tests/test_sdlc.py`, marked portable.
- **R2:** `test_upgrade_refuses_and_writes_nothing`, parametrised over Tier 2, stage `design`, an
  id naming another change, and the base branch.
- **R3:** `test_verdicts_names_upgrade_on_an_upgrade_answer`,
  `test_only_a_decided_blocking_answer_upgrades` (open, default, superseded and other-answer
  lines), and `test_a_tier_2_answer_never_upgrades`.
- **R4:** `test_upgrade_writes_the_record_then_the_tier`, `test_upgrade_moves_no_head` and
  `test_an_upgrade_cut_short_finishes_on_rerun`. All need `uv`, since they run the real `sdlc.py`.
  A refusal from `verdicts` is in the first.
- **R4, also:** `test_a_bad_upgrade_record_stops_the_run`, parametrised over a garbled first line
  and a decision that isn't an upgrade answer.
- **R5:** `test_no_second_upgrade`.
- **R6:** `test_an_upgraded_run_specs_then_builds_round_p` and
  `test_an_upgraded_run_counts_its_rounds_from_p`.
- **R7:** `test_the_spec_prompt_names_the_upgrade`.
- **R8:** `test_the_upgraded_build_resumes_the_builder_into_round_p`.
- **R9:** `test_decided_refuses_while_an_upgrade_is_under_way`.
- **R10:** `test_reviewers_and_approver_are_told_of_the_upgrade`.
- **R11:** `test_start_reports_an_upgrade` and `test_fresh_holds_an_upgraded_run`.
- **R12:** `test_check_leaves_out_the_template_plan_during_a_live_upgraded_build`,
  `test_the_template_plan_shows_once_the_upgraded_build_is_not_live`, and
  `test_the_upgraded_record_pattern_is_a_pinned_copy`, in `tests/test_sdlc.py` beside 105's
  tests, all portable.
- **R13:** `test_an_upgrade_or_spec_record_keeps_the_step_it_paused_at` in
  `tests/test_factory.py`, and `test_an_upgrade_pauses_the_step_track` in `tests/test_board.py`,
  which also pins `PAUSES`.
- **R14:** `test_the_build_skill_handles_every_step_verdicts_names` in `tests/test_skills.py`. It
  reads every step `loop_state()` assigns from its source and asks for a `- **\`<step>\`**`
  bullet in the skill. The existing skill tests cover the one `WAIT` and the `Bash(...)` rule.
- **R15:** an acceptance check in `checks.md`, since only a revert could undo prose. It asks
  that each doc names the upgrade, and that none of the factory's docs says "promot".
- **Manual:** the scratch-repo walk in the spec's Verification section, which these tests
  automate end to end in R4 and R6.

## Rollback

`git revert` undoes everything here: two scripts, the board, one skill, one agent definition, the
docs and the tests. Nothing is published or written outside the repo.

A change upgraded while this was live keeps what it was given after a revert:

- `tier: 2` and `stage:`.
- `spec.md` and `plan.md`.
- `build/round-<P>.upgraded.md`.

That is a valid Tier 2 change, and `check` reads it as one. The record file becomes inert. The
reverted `factory.py` doesn't read it, and its numeric-stem filters skip it as a round. To go
back by hand, delete the record file. Edit `tier:` back to `1` only if the spec is also dropped.
