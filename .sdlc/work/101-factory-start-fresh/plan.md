---
id: 101
slug: factory-start-fresh
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 101 — Factory builds start current and share the gate · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`: `cmd_start` gains `base` and `behind` (R1); new
  `cmd_fresh()` and its `fresh` subcommand, delegating to `_sdlc(["base", ...])` and
  `_sdlc(["resolve", ...])` exactly as `cmd_land()` delegates `base` (R2–R5); `DEFAULTS["gate_jobs"]`,
  `_gate_jobs()` read through `_base_factory()` like `_land()`, set in `load_config()` with the
  `mode`-style "applies once it lands" warning (R7); `_slot_dir()`, `_try_lock()`, `_unlock()`
  (platform imports inside), `gate_slot()` context manager, and `cmd_gate()` running the check
  inside it, `waited` in its JSON (R8–R11); the docstring (R12).
- `plugins/factory/skills/build/SKILL.md`: Step 0 runs `fresh <NNN>` after a clean `start`, keeps
  its `head`; Step 1 shows `behind` and what `fresh` did; the new `Bash(...)` rule (R6).
- `plugins/factory/README.md`: `gate_jobs` in the config block; `fresh` and the slots under
  *Rounds that converge* and *Mechanism* (R12).
- `AGENTS.md`: *Writes before a WAIT* names the fourth exception; *The factory* says `fresh`
  moves a change's branch through `sdlc`'s own `base` and `resolve` (R12, Contracts touched).
- `tests/test_factory.py`: the R1–R5 and R7–R10 tests named in the spec.
- `tests/test_skills.py`: `test_build_brings_the_change_up_to_date_before_its_spec_writer` (R6).

Reused, not re-derived: `_base()`, `_git()`, `_base_factory()`, `find_change()`,
`frontmatter()`, `restart_state()`, `_sdlc()`/`sdlc_path()`, `cmd_land()`'s handling of `base`'s
JSON. `sdlc.py`'s `cmd_base()` and `cmd_resolve()` hold every git step `fresh` takes; `factory.py`
adds none.

## Work order

1. **`start` reports `behind`** (R1): test, then the two keys in `cmd_start()`.
2. **`fresh` fast-forwards** (R2, R5): the fast-forward test in a real `sdlc.py new --worktree`
   change, and the stubbed `sdlc_path()` refusal; `cmd_fresh()` and its subcommand.
3. **`fresh` holds a stopped run** (R3): test at `stage: build`; the `held` branch.
4. **`fresh` resolves or stops** (R4): both cases; the `resolve` / `resolve --abort` path.
5. **`gate_jobs` read from the base** (R7): test; `_gate_jobs()` and `load_config()`; existing
   config-default test updated for the new key.
6. **Gate slots** (R8–R11): the kill test against `gate_slot()`, then the two-gates test at
   limits 1 and 2; `gate_slot()` and its use in `cmd_gate()`, `waited` in the JSON.
7. **The build skill** (R6): the skills test, then Step 0/Step 1 text and the rule.
8. **Docs** (R12): README, docstring, AGENTS.md. Then `./check.sh`.

## Tests

- R1: `test_start_says_how_far_behind_the_base_the_change_is`.
- R2: `test_fresh_fast_forwards_a_change_behind_the_base` (needs uv, runs the real `sdlc.py`).
- R3: `test_fresh_holds_a_run_that_stopped_part_way`.
- R4: `test_fresh_resolves_what_git_can_and_stops_on_a_real_conflict`, cases (a) and (b).
- R5: `test_fresh_refuses_without_its_own_sdlc`.
- R6: `test_build_brings_the_change_up_to_date_before_its_spec_writer` in `tests/test_skills.py`,
  plus the existing rule/command tests.
- R7: `test_gate_jobs_is_read_from_the_base_branch_and_checked`.
- R8, R9: `test_two_gates_with_a_limit_of_one_run_one_after_the_other` (limit 1 and limit 2).
- R10: `test_a_killed_gate_frees_its_slot` (`portable`).
- R11: the existing import scan in `tests/test_windows.py`.
- R12: no test; ship's context-doc pass.

## Rollback

`git revert` undoes all of it. Outside the tree: the slot files
`<git common dir>/sdlc-factory-gate-<k>.lock` stay behind once any gate has run; they are empty
and harmless, removed by `rm "$(git rev-parse --git-common-dir)"/sdlc-factory-gate-*.lock`. A
`fresh` that moved a change's branch printed its `undo` (`git -C <tree> reset --keep <from>`, or
`sdlc.py resolve <change> --abort`), which a revert of this change does not run.
