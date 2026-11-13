---
id: 054
slug: close-runs-cleanup
kind: plan
created: 2026-11-13
updated: 2026-11-13
---

# 054 — Close runs the repo's cleanup when its gate approves it · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `commands.close_cleanup_runs` (and `BOOL_KEYS`); `load_config()`'s key loop
  split into `_apply_config()`, a warning for a switch with no command; `_config_at(home, ref)`;
  `_cleanup_plan()`; `CLEANUP_TIMEOUT`; `cmd_close()` reports `cleanup` and runs it last.
- `skills/close/SKILL.md`: Steps 1, 2 (both questions), 4, Out of scope and the description.
- `docs/REFERENCE.md`: the key, the `!` rule, the commands `sdlc.py` runs itself.
- `AGENTS.md`: the **Closing** paragraph names the `cleanup` step.
- `.sdlc/setup.json`: rewritten by `sdlc.py record`, so it lists the new key.
- `tests/test_cleanup.py` (new): R1–R8, harness from `tests/test_push.py`.
- `tests/test_skills.py`: `READS_CONFIG["sdlc:close"]` gains the key; the close-skill test pins
  the question's cleanup clause.

## Work order

1. Config: the key, `BOOL_KEYS`, `_apply_config()` split out of `load_config()` unchanged in
   behaviour, the R1 warning, `_config_at()`. Run the existing config tests.
2. `cmd_close()`: `_cleanup_plan()` from the base ref's config (shipped: `refs/sdlc/base/<branch>`
   when it exists, else `cfg` while not landed, else unreadable; dropped: `cfg`), reported as
   `cleanup` before `--check` returns; `cleanup()` beside `push()`, modelled on `after_bump()`,
   called on the success path after the push, before `emit(0)`. Run the close and push tests.
3. `tests/test_cleanup.py`.
4. The skill, then `tests/test_skills.py`.
5. `docs/REFERENCE.md`, `AGENTS.md`, then `sdlc.py record`, then `./check.sh`.

## Tests

The cleanup command in tests writes a marker (`touch "<tmp>/ran-{id}"`), so whether and when it
ran is observable.

- **R1:** `test_config_warns_on_a_switch_with_no_command`, and a non-bool value warns and reads
  false.
- **R2, R6:** `test_check_names_the_command_and_runs_nothing`: `--check` and the real close
  report the same filled, stripped command; no marker after `--check`.
- **R3:** `test_runs_last_after_the_worktree_and_branch_are_gone` (`done[-1] == "cleanup"`, after
  `push`); `test_a_dropped_change_runs_it_too`.
- **R4:** `test_a_leading_bang_is_stripped`: `"! false"` is `cleanup_failed`.
- **R5:** `test_a_failed_cleanup_never_fails_the_close`: a non-zero exit and a timeout, exit 0,
  landed.
- **R6:** `test_a_failed_step_never_reaches_the_cleanup`: a failing archive command, exit 1, no
  marker.
- **R7:** `test_a_change_cannot_turn_on_its_own_cleanup`: its own close doesn't run it, the next
  does.
- **R8:** `test_off_by_default_hands_over_and_runs_nothing`, and the existing close tests
  untouched.
- **R9:** `tests/test_skills.py`. **R10:** `sdlc.py drift` reports nothing; `./check.sh`.

## Rollback

`git revert` of the change's commit removes the key and the step. A host that set
`close_cleanup_runs` then gets an `unknown key` warning and the hand-over back. What a cleanup
already deleted in a host isn't covered: that is the host's own command, run behind its own yes.
