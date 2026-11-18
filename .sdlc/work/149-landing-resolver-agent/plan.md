---
id: 149
slug: landing-resolver-agent
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 149 — A landing's conflicts are resolved by an agent of their own, measured apart from the builder · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/agents/resolver.md` (new): the resolver's prompt: tools `Read, Grep, Glob, Edit,
  Bash`, model `sonnet`, merging rules taken from `builder.md`'s *A conflict, while landing*.
- `plugins/factory/agents/builder.md`: loses *A conflict, while landing*.
- `plugins/factory/scripts/factory.py`:
  - `ROLES` gains `resolver`; `FIXED_MODELS["resolver"] = "sonnet"`;
    `TASK_ROLE["train-resolve"] = "resolver"`; `RESOLVE_RECORDS` gains `runs/resolver.sessions`.
  - `cmd_agent`: refuse `train-resolve` with a `--role` other than `resolver`, before anything is
    written; argparse's `--role` choices gain `resolver`.
  - `cmd_resolve --continue`: the fence (R8, R9) after the conflict-marker check, through a new
    `_status_entries()` (sibling of `_dirty()`, keeping each entry's `XY`); refusal through the
    existing `_land_refused()`.
  - `_conflicted()` (R14): reads `git diff --name-only --diff-filter=U -z` raw, so a non-ASCII
    path comes back as it is named.
  - Words only: `_land_task`'s docstring, the `RESUMES` comment, `cmd_resolve`'s docstring,
    `land-review`'s prompt ("resolved while landing", not "by the builder").
- `plugins/factory/README.md`: agents table row, the editor line, the landing paragraph, the
  model line.
- `plugins/factory/skills/land/SKILL.md`: the `resolve` step names the resolver.
- `plugins/factory/skills/build/SKILL.md`: the `models_at` line names the resolver's sonnet.
- `AGENTS.md` (*The factory*): "only the builder and the resolver edit".
- `scripts/sdlc.py`: `_unmerged()` reads the same `-z` listing (R14).
- `scripts/board.py`: no code (it reads no role list; a `resolver` cost row falls through
  `step_samples()` as a landing builder row did); its comments, and the card's `next:` line
  ("its agent is resolving a conflict", round 1's kept ux change), say "agent" where they said
  the builder resolves; `tests/test_board.py` and `docs/REFERENCE.md`'s board paragraph follow.
- Tests:
  - `tests/test_train.py`: `test_a_train_conflict_goes_to_one_agent_with_every_change` renamed
    `test_a_train_conflict_goes_to_the_resolver_with_every_change` and updated (R1, R2, R3, R10);
    new `test_train_resolve_runs_no_role_but_the_resolver` (R4) and
    `test_a_resolution_outside_its_files_is_refused` (R8, R9).
  - `tests/test_skills.py`: `AGENT_TOOLS["resolver"]`, `NEVER_RUNS_CHECKS["resolver"]`, the
    comment (R5, R6, R13).
  - `tests/test_factory.py`: `test_the_resolver_has_a_model_of_its_own` (R7),
    `test_a_resolver_session_is_its_own_role` (R12).
  - `tests/test_train.py`: `test_a_train_conflict_in_a_non_ascii_path_resolves` (R14), and
    `test_train_run_starts_a_rounds_reviewers_together`'s stand-in plan keyed to `resolver`.
  - `tests/test_resolve.py`: `test_a_conflict_in_a_non_ascii_path_is_resolved` (R14, `sdlc.py`).
  - `tests/test_land.py`: the `land-fix` tests already assert the builder (R11); checked, not
    changed unless they don't.

Reused, not re-derived: `agent_name()`, `model_for()`, `record_cost()`, `_land_refused()`,
`_conflicted()`, `_dirty()`'s `-z` parsing, `sdlc._agent_sessions()`.

## Work order

1. **The role.** Tests for R1–R3, R7, R12 (red), then `ROLES`, `FIXED_MODELS`, `TASK_ROLE`,
   `RESOLVE_RECORDS` and `resolver.md` (green). The train conflict test passes end to end.
2. **The role guard (R4).** Test first, then the refusal in `cmd_agent` and the argparse choice.
3. **The fence (R8, R9).** Test first (a stray tracked edit, a stray untracked file, and a clean
   resolution beside a cleanly staged second file), then `_status_entries()` and the check in
   `--continue`.
4. **Non-ASCII conflicted paths (R14).** Both tests first, then `_conflicted()` and
   `_unmerged()` read with `-z`.
5. **The words (R5, R6, R13).** `AGENT_TOOLS`, `NEVER_RUNS_CHECKS` first, then `resolver.md`'s
   rules, `builder.md`'s section removed, README, AGENTS.md, the land and build skills, the
   prompts and docstrings. `./check.sh`.

## Tests

- R1, R2, R3, R10: `test_a_train_conflict_goes_to_the_resolver_with_every_change` (argv names
  `sdlc-factory:resolver`, `--session-id`; `role == "resolver"`; `builder.sessions` byte for byte
  unchanged; a `resolver` cost row with its model and no new `builder` row; `resolver.sessions`
  committed in `HEAD` and clean; an untouched non-conflicted file hashes the same).
- R4: `test_train_resolve_runs_no_role_but_the_resolver`.
- R5, R6: `test_agents_have_their_tools_and_nothing_more`, `test_no_agent_but_the_builder_runs_checks`.
- R7: `test_the_resolver_has_a_model_of_its_own`.
- R8, R9: `test_a_resolution_outside_its_files_is_refused`.
- R11: `test_a_fix_asked_at_landing_is_built_gated_and_reviewed_at_depth` (`tests/test_land.py`),
  which already pinned the resumed builder session, now also asserts `role == "builder"`.
- R12: `test_a_resolver_session_is_its_own_role`.
- R13: `./check.sh`, and `checks.md`'s acceptance check (the docs' words, which only a revert
  could break).
- R14: `test_a_train_conflict_in_a_non_ascii_path_resolves`,
  `test_a_conflict_in_a_non_ascii_path_is_resolved`.

## Rollback

`git revert` covers it all. Nothing is written outside the repo. A change landed while this was in
place keeps `runs/resolver.sessions` and `Sdlc-Role: resolver` on its `Close` commit, and history
is never rewritten: after a revert those stay as they are and read as a role of their own; a
`[models] resolver` line a host added would then warn as an unknown role until removed.
