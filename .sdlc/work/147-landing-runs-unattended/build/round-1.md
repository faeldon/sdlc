I built change 147 test-first: after the yes, `factory.py train --run` lands the train on its own and stops only where the person is needed. The gate (`./check.sh`) passes: 2683 tests, 18 skipped. Nothing is committed.

## Slices built

1. **R16, why each ejection happened.** Every `eject` reading now carries a `cause`: `gate`, `review` or `refusal`. `--eject` keeps it in `ejections` and in its output. An old state file with no cause reads as `refusal`, so it pauses rather than ejecting.
2. **R13, `resolve` always names its target.** The bare `resolve <NNN>` is gone: the command takes exactly one of `--onto` and `--continue`, in the code and on the command line. Outside a train, `--onto` accepts only the base branch (by name or by its tip) and writes no train state and no landing round. The rebase loop that settles `.sdlc/last-id` now lives once, in `_rebase_settling()`.
3. **R14, a resolution leaves the worktree clean.** `--continue` now writes `runs/land-resolved` before the rebase continues, and stages it with `build/land-<n>.md` and the other records. If a second conflict aborts the rebase, the abort removes the marker too.
4. **R15, one test driver.** `tests/train_driver.py` holds `drive_train()`, the stand-in reply writers and a fake `claude` that answers by agent and by change. Neither test file keeps its own driver now.
5. **R6 and R7, one loop at a time.** `train --run` holds a lock on `sdlc-factory-train-run.lock` in the git common dir, on an open descriptor, so the lock is freed however the process ends. Its child commands are marked through `TRAIN_RUN_ENV` so they go ahead. While the lock is held, a second `--run`, `--begin`, `--eject` or `--stop` refuses, and a plain reading answers `running: true` without writing anything. `--cancel` is checked between steps.
6. **R1–R5 and R10, the loop.** Each step is a subprocess of the script, limited to the commands in `RUN_STEPS`. It ejects a change only when the gate found it at fault, and stops at every other stop R4 lists. Reviewers in the same round start together. Each stop is recorded with its reason and the way on in the change's `runs/land-step.md`.
7. **R9, the stored fix.** `train --begin … --fix <NNN>=R<n>` works only with `--by person`, and checks that the line exists in that change's `decisions.md`. The fix is made once, at that change's close.
8. **R8, a killed loop resumes.** Tested by killing the loop mid-run and rerunning it (details below).
9. **R11 and R12, the skill and the docs.** The land skill now runs `accept` and `cases` behind the harness's prompt, begins the train, starts `train --run` with `run_in_background`, reports the result when it exits, and on a rerun takes the one step the person was asked for. Its Bash rules are cut to four commands: `config`, `sdlc-path`, `land-check` and `train`. The factory README, `docs/REFERENCE.md`, `AGENTS.md` and the build skill are updated, and none of them asks for "a session of its own" any more.

## Tests added

- **Loop (R1–R10):**
  - `test_train_run_lands_a_batch_of_three` (R1)
  - `test_train_run_records_each_step` (R2)
  - `test_the_loop_runs_only_its_named_commands`, marked portable (R3)
  - `test_train_run_never_runs_a_prompted_command` (R3)
  - the four stop tests: `_stops_at_a_kept_change`, `_at_a_refusal`, `_at_a_refused_push`, `_when_nothing_moves` (R4)
  - `test_train_run_ejects_a_gate_fault_and_lands_the_rest` and `test_train_run_resumes_after_a_kept_change` (R5)
  - `test_a_second_train_run_refuses_while_one_runs` (R6)
  - `test_train_run_cancels_between_steps` (R7)
  - `test_a_killed_train_run_resumes` (R8): it kills the loop's process group while a stand-in reviewer is blocked, then reruns it.
  - `test_train_run_makes_the_stored_fix_once` (R9)
  - `test_train_run_starts_a_rounds_reviewers_together` (R10): every reviewer starts before any finishes.
- **Skill and docs (R11, R12):** `test_land_runs_the_train_unattended`.
- **`resolve` (R13, R14):**
  - `test_resolve_needs_onto_or_continue` and `test_resolve_onto_the_base_outside_a_train` (R13)
  - `test_a_resolution_leaves_the_worktree_clean` and `test_a_failed_resolution_leaves_no_marker` (R14)
- **Shared driver and causes:**
  - `test_the_train_driver_takes_every_step_a_reading_names` (R15)
  - `test_every_ejection_names_its_cause` (R16)
- **Rewritten:**
  - the two register-conflict tests and the cost-line test now use `--onto main`;
  - `test_the_land_skill_names_its_mend` became `test_the_landing_loop_names_its_mend`, because the skill no longer has that bash block;
  - the fix test in `test_skills.py` now checks `--fix <NNN>=R<n>`.

## Changes to `plan.md`

I wrote it first, then changed it during the build. Two changes from the spec's design are recorded in its *Departures* section:

- **No `train --fixed` command.** R3's list of commands doesn't include one. Instead the reading names a `fix` step, with `ask` and `asked`, and `land-fix --ask` and `land-fix --commit` mark the train's state themselves. A loop killed partway through a fix skips the second `--ask` when it resumes.
- **The no-progress rule** compares the step, the change and the bytes of the state file, as R4 words it.

## `notes.md`

Two unticked items:

- The board could read the run lock to show a landing running unattended.
- The kill test can't run on Windows, because it kills a process group.

## Evidence

$ ./check.sh > /tmp/147-gate.log 2>&1; echo "exit: $?"; grep -E "passed|failed|error|Would reformat|Found" /tmp/147-gate.log | head
exit: 0
All checks passed!
2683 passed, 18 skipped in 135.93s (0:02:15)
⚠ Found 1 plugin directory warning:
✔ Validation passed
⚠ Found 1 plugin directory warning:
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q -m portable -n auto
508 passed, 18 skipped in 15.32s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_train.py tests/test_land.py tests/test_factory.py tests/test_skills.py -k "train_run or second_train_run or killed_train_run or every_ejection or resolve_needs or resolve_onto_the_base or resolution_leaves or failed_resolution or driver_takes or loop_runs_only or land_runs_the_train or cost_line or landing_resolution_never or loop_names_its_mend or fixs_id"
27 passed in 103.00s (0:01:43)
exit: 0

$ grep -rn "def _drive(\|def _land_train(" tests/ | grep -v "own = \["
(no output)
exit: 1

$ uv run --group dev pytest -q tests/test_nothing_local.py
8 passed in 1.59s
exit: 0
