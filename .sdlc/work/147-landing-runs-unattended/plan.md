---
id: 147
slug: landing-runs-unattended
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 147 — A landing runs unattended after its one yes · plan

> Written after reading `factory.py`'s train (`cmd_train()`, `_train_reading()`, `_train_gate()`,
> `_train_eject()`, `cmd_resolve()`, `cmd_land_close()`, `cmd_land_fix()`, the gate slots' lock
> helpers), the land skill, and the two test drivers (`tests/test_train.py`'s `_drive()`,
> `tests/test_land.py`'s `_land_train()`).

## Files to change

- `plugins/factory/scripts/factory.py`:
  - `_train_reading()`: every `eject` carries `cause` (`gate`, `review`, `refusal`), kept as
    `fault_cause` beside `fault`; the reading's `ejected` list is built from `state["ejections"]`
    with each one's `cause`; the reading carries `gates` (how many attempts the train recorded);
    a new `next: fix` at the close step of the change a stored fix names (R9).
  - `_train_eject()`: copies the cause into `ejections`, clears `fault_cause`.
  - `cmd_train()`: `--run`, `--cancel`, `--fix NNN=R<n>` on `--begin`; the run-lock check
    (`train_running()`), skipped when `TRAIN_RUN_ENV` is set.
  - New: `TRAIN_RUN_LOCK`, `TRAIN_CANCEL`, `TRAIN_RUN_ENV`, `TRAIN_STEPS`, `RUN_STEPS`,
    `RUN_STOPS`, `train_running()`, `_train_run()` (the lock), `_run_loop()`, `_run_step()`,
    `_run_group()`, `_run_stop()`.
  - `cmd_land_fix()`: in a train whose stored fix names the change, `--ask` records the round it
    opened and `--commit` marks the fix done, in the train's state.
  - `cmd_resolve()`: needs exactly one of `--onto` and `--continue` (argparse group too); `--onto`
    outside a train takes only the base branch (name or tip) and rebases from the merge base,
    `current` / `stacked` / `conflict`, writing no train state and opening no round; the rebase
    loop with the counter settling itself is `_rebase_settling()`, called by both `--onto` forms;
    `--continue` writes `runs/land-resolved` first and stages it and `build/land-<n>.md` with
    `RESOLVE_RECORDS` (R14). The docstring's bare-form line goes.
  - Module docstring: `train --run`, `--cancel`, the run lock file.
- `tests/train_driver.py` (new): `drive_train(factory, root, capsys, …)`, the stand-in writers
  (`verdict()`, `verified()`, `asked()`), `DRIVER_STEPS`, and the fake `claude` the loop's tests
  put on `PATH` (`FAKE_CLAUDE`, `fake_claude()`), which answers by agent and change.
- `tests/test_train.py`: `_drive()` and its helpers go; tests call `drive_train`. New tests for
  R1–R10, R15, R16.
- `tests/test_land.py`: `_land_train()` goes (callers use `drive_train(..., strict=True)`);
  `_resolving()` uses `--onto main`; R13 and R14 tests; `test_the_land_skill_names_its_mend`
  now reads the mend from `RUN_STEPS`.
- `tests/test_factory.py`: `test_a_cost_line_written_mid_rebase_goes_into_the_resolved_commit`
  uses `--onto main`.
- `tests/test_skills.py`: `test_the_land_skill_passes_a_fixs_id_never_its_words` follows the fix
  to `--begin … --fix <NNN>=R<n>`; new `test_land_runs_the_train_unattended`.
- `plugins/factory/skills/land/SKILL.md`: rules cut to `config`, `sdlc-path`, `land-check`,
  `train *`; Step 3 rewritten (before-commands behind the prompt, the fix line, `--begin`,
  `train --run` in the background, the report, the resume); the description and the "session of
  its own" paragraph.
- `plugins/factory/README.md`, `docs/REFERENCE.md`, `AGENTS.md` (factory paragraph): the loop,
  `--cancel`, the run lock, the stops, which ejections the loop makes. `plugins/factory/skills/
  build/SKILL.md`'s "from a session of its own" pointer to land.

## Work order

1. **R16, the cause.** Tests first (`test_every_ejection_names_its_cause`), then `fault_cause` in
   `_train_reading()`, `ejections` in `_train_eject()`. Every existing train test still passes.
2. **R13, `resolve --onto <base>`.** Tests (`test_resolve_needs_onto_or_continue`,
   `test_resolve_onto_the_base_outside_a_train`), then `_rebase_settling()` and the outside-train
   path; rewrite the register-conflict tests and the cost-line test to `--onto main`.
3. **R14, a clean resolution.** Tests (`test_a_resolution_leaves_the_worktree_clean`,
   `test_a_failed_resolution_leaves_no_marker`), then the marker written and staged before
   `--continue`.
4. **R15, the shared driver.** Move `_drive()`/`_land_train()` into `tests/train_driver.py`, with
   a `fix` step; `TRAIN_STEPS` in the script; `test_the_train_driver_takes_every_step_a_reading_names`.
5. **R6, R7, the run lock and cancel.** `test_a_second_train_run_refuses_while_one_runs`, then
   `train_running()`, the checks in `cmd_train()`, `--cancel`.
6. **R1–R5, R10, the loop.** The fake `claude` in the driver module; tests
   (`lands_a_batch_of_three`, `records_each_step`, `never_runs_a_prompted_command`, the four
   stops, `ejects_a_gate_fault`, `resumes_after_a_kept_change`, `starts_a_rounds_reviewers_together`,
   `cancels_between_steps`), then `_run_loop()`.
7. **R9, the stored fix.** `test_train_run_makes_the_stored_fix_once`, then `--fix` on `--begin`,
   `next: fix`, and `land-fix`'s state marks.
8. **R8, a kill.** `test_a_killed_train_run_resumes` (a subprocess loop, SIGKILLed while a stand-in
   reviewer blocks).
9. **R11, R12, the skill and the docs.** `test_land_runs_the_train_unattended`, the skill, the docs.

## Departures from the spec's design

- **No `train --fixed`.** The design had the loop mark the fix done through a new `train --fixed
  <NNN>`; R3's list of commands names no such command. Instead the reading names the fix as its
  own step, `next: fix` (with `ask` and `asked`), at that change's close, and `land-fix` itself
  marks the train's state: `--ask` records the round it opened, `--commit` marks it done. A loop
  killed mid-fix resumes it: `asked` skips the second `--ask`. `fix` joins `TRAIN_STEPS`.
- **No-progress** compares the reading's `next` and `change` and the state file's bytes after the
  reading, as R4 words it.

## Tests

- R1: `test_train_run_lands_a_batch_of_three`.
- R2: `test_train_run_records_each_step`; the stop record in `test_train_run_stops_at_a_kept_change`.
- R3: `test_train_run_never_runs_a_prompted_command`; `test_the_loop_runs_only_its_named_commands`
  (portable: `RUN_STEPS`, `RUN_EJECTS` and `RUN_STOPS` as the spec lists them).
- R4: `test_train_run_stops_at_a_kept_change`, `_at_a_refusal`, `_at_a_refused_push`,
  `_when_nothing_moves`.
- R5: `test_train_run_ejects_a_gate_fault_and_lands_the_rest`,
  `test_train_run_resumes_after_a_kept_change`.
- R6: `test_a_second_train_run_refuses_while_one_runs`.
- R7: `test_train_run_cancels_between_steps`.
- R8: `test_a_killed_train_run_resumes`.
- R9: `test_train_run_makes_the_stored_fix_once`.
- R10: `test_train_run_starts_a_rounds_reviewers_together`.
- R12 also: `test_the_landing_loop_names_its_mend` (was `test_the_land_skill_names_its_mend`,
  whose bash block the skill no longer has).
- R11: `tests/test_skills.py`'s rule checks; `test_land_runs_the_train_unattended`.
- R12: `test_land_runs_the_train_unattended` reads the docs' words; the gate.
- R13: `test_resolve_needs_onto_or_continue`, `test_resolve_onto_the_base_outside_a_train`, the
  rewritten register-conflict and cost-line tests.
- R14: `test_a_resolution_leaves_the_worktree_clean`, `test_a_failed_resolution_leaves_no_marker`.
- R15: `test_the_train_driver_takes_every_step_a_reading_names`; no `def _drive` or
  `def _land_train` left.
- R16: `test_every_ejection_names_its_cause`.
- Manual (the spec's *By hand, once*): a scratch host, `/sdlc-factory:land`, the loop in the
  background; `train` from another terminal says `running: true`; `train --cancel` mid-run.

## Rollback

`git revert` undoes the code, the skill and the docs. Not covered: a train's state file
(`sdlc-factory-train.json`) written by this version may carry `fault_cause`, `fix` and an
`ejections` entry with `cause`; the old reader ignores unknown keys, so nothing to undo. A run
lock file `sdlc-factory-train-run.lock` and a cancel file `sdlc-factory-train.cancel` may be left
in the git common dir: `rm "$(git rev-parse --git-common-dir)"/sdlc-factory-train-run.lock
"$(git rev-parse --git-common-dir)"/sdlc-factory-train.cancel`. Nothing is published.
