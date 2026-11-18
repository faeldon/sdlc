---
id: 147
slug: landing-runs-unattended
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 147 — A landing runs unattended after its one yes · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions, each checked in the code:

- `factory.py train` (`cmd_train()`, `_train_reading()`) already names every next step. It keeps the train's state in `sdlc-factory-train.json` in the git common dir.
- Every step it names is a `factory.py` subcommand that is safe to rerun (139's R11, R12 and R19). `tests/test_train.py`'s `_drive()` and `tests/test_land.py`'s `_land_train()` run those steps the way the skill does.
- An ejection reading comes from one of three places in `_train_reading()`:
  - `_train_gate()`: the last change of the first red prefix;
  - a landing round that `land_verdict()` ends in `stop`: a kept change, a used-up mend, an unreadable reply, or acceptance checks that fail as stacked;
  - a refusal: `failed`, recorded by `_train_fail()`, or `_land_readiness()`'s refusal.
- The question the person approved already promises the first of those: "a red tip bisected, the change at fault left out with why and the rest landed".
- `factory.py accept` and `cases` are kept out of the land skill's `allowed-tools` on purpose, so the harness prompts before each run.
- The gate slots' lock helpers (`_try_lock()`, `_unlock()`, `_slot_dir()`) hold a lock on an open descriptor in the git common dir, on both platforms.
- A fake `claude` on `PATH` already stands in for agents in `tests/test_factory.py`.
- No skill or script runs `factory.py resolve` without `--onto`. Factory's `fresh` runs `sdlc.py resolve`. Only `tests/test_land.py`'s register-conflict tests and `test_a_cost_line_written_mid_rebase_goes_into_the_resolved_commit` call the bare form.
- After `resolve --continue`, `build/land-<n>.md` and `runs/land-resolved` are left uncommitted. Only `RESOLVE_RECORDS` is staged before the rebase continues, and the marker is written after it.

1. **R1. The loop lands the batch.** `factory.py train --run` takes the step each reading names, through the same command the land skill runs today, then reads again. It stops when the reading says `done`, or at one of R4's stops.
   - Test `test_train_run_lands_a_batch_of_three`: a batch of three in a scratch repo, with stand-in agents (a fake `claude` on `PATH`). One call ends `done`, with three `Close` commits on the base branch's first-parent line, in order.
2. **R2. Each step is recorded where the board reads it.** The command that takes a step records it in the change's `runs/land-step.md`, as now (`_record_land()`). When the loop stops at a change, it also records a `stop` there, naming the step and the way on.
   - Test `test_train_run_records_each_step`.
3. **R3. The loop runs only these commands:**
   - `land --by`;
   - `resolve --onto`;
   - `agent --task train-resolve`, then `resolve --continue`;
   - `gate --land`;
   - `train --eject <NNN>`, only when the reading's `cause` is `gate` (R16);
   - `agent --task land-review|land-verify|land-mend`;
   - `land-fix --ask`, `agent --task land-fix` and `land-fix --commit`, only for a fix stored at `--begin` (R9);
   - `land --close`.

   It never runs `accept`, `cases` or `train --stop`, and never `train --eject` for any other cause.
   - Test `test_train_run_never_runs_a_prompted_command`: `RUN_STEPS` names exactly these, and a run over a change with an acceptance check never writes `build/land-accept.md`.
4. **R4. The loop stops at the first of these.** It exits non-zero and changes nothing more. Its output has `stopped`, naming `next`, `change`, `reason` and `way_on`. The stops:
   - a reading that names `eject` with `cause` `review` (a kept change, a used-up mend, an unreadable reply, checks failing as stacked) or `refusal`;
   - a reading that names `stop` (past `land.moves`, or the first change at fault twice in a row);
   - a reading that names `accept`;
   - a reading that names `commit` with a non-empty `before`;
   - a reading that names `resolve` with no conflicted `files`;
   - a `land --close` that reports `push_failed` (the change has landed);
   - any step command that exits non-zero, except `gate --land` and a close that reports `moved`;
   - an agent session that reports a `problem`;
   - the same step named for the same change twice in a row, with the train's state unchanged.

   Tests:
   - `test_train_run_stops_at_a_kept_change`: the landing reviewer of change two keeps a change. The run exits naming `eject`, cause `review`, change two. Two is still at its stacked commit, and two and three aren't closed.
   - `test_train_run_stops_at_a_refusal`
   - `test_train_run_stops_at_a_refused_push`
   - `test_train_run_stops_when_nothing_moves`
5. **R5. A gate fault is ejected and the rest land; a rerun resumes.** When the reading names `eject` with cause `gate`, the loop runs `train --eject` and reads again. The rest of the train re-stacks and is gated again, as 139 does. The stop-twice rule of `_train_gate()` still ends the train. A rerun of `train --run` resumes from the saved state. A resumed skill gets past a stop only through the command the reading names.
   - Test `test_train_run_ejects_a_gate_fault_and_lands_the_rest`: a check fails whenever change two's file exists. One `train --run` ends `done` with one and three landed. Two is back at its pre-train commit, its committed `runs/land-step.md` says `eject` and names its gate file, and the exit JSON lists it under `ejected` with cause `gate`.
   - Test `test_train_run_resumes_after_a_kept_change`: after R4's stop, `train --eject <two>` and then `train --run` land one and three.
6. **R6. Only one loop at a time.** For its whole life, `train --run` holds a lock on `sdlc-factory-train-run.lock` in the git common dir. The lock is held on an open descriptor, so the OS frees it however the process ends. The loop sets `TRAIN_RUN_ENV` in its children's environment, as `sdlc.py`'s `LOCK_HELD_ENV` does, so its own `train` readings and `--eject` go ahead. Without that marker, while the lock is held:
   - a second `--run`, `--begin`, `--eject` or `--stop` refuses;
   - a plain `train` reading reports `running: true` and writes nothing.

   Test `test_a_second_train_run_refuses_while_one_runs`: it checks each refusal, that the state file's bytes don't change, and that each call goes ahead with the marker set.
7. **R7. A cancel waits for the step in flight.** `train --cancel` writes `sdlc-factory-train.cancel` in the git common dir. The loop checks for it only between steps. When it finds it, the loop exits with `stopped.next == "cancel"`, removes the file, and leaves the train under way. With no loop running, `--cancel` refuses.
   - Test `test_train_run_cancels_between_steps`.
8. **R8. A killed loop resumes.** A kill at any point leaves state that a rerun resumes from, never a half-landed change.
   - Test `test_a_killed_train_run_resumes`: a stand-in agent blocks until the test SIGKILLs the loop. A second `train --run` ends `done`, every change is closed once, and no branch carries another change's commit.
9. **R9. A fix asked for in the yes is made once.** `train --begin … --fix <NNN>=R<n>` (with `--by person` only) stores the fix in the train's state. The skill writes the person's words to `decisions.md` before `--begin`, never on a command line. The loop makes the fix once, at that change's `close` step, then reads again.
   - Test `test_train_run_makes_the_stored_fix_once`.
10. **R10. A round's agents start together.** When a landing round is missing several roles, the loop starts their `agent` sessions together and waits for all of them.
    - Test `test_train_run_starts_a_rounds_reviewers_together`.
11. **R11. The skill asks first, then backgrounds the loop.** The land skill asks the question in its dialog. Then, behind the harness's prompt, it runs each `before` command (`factory.py accept`, `cases`) for each change. Then it runs `train --begin`, and starts `train --run` in the background. When the loop exits, the skill reports its JSON, including each gate ejection it made with its reason, and the reason and way on at a stop. A rerun of the skill resumes: it runs the one command the reading names (`--eject` for a non-gate cause, `--stop`, or `accept`), then `train --run` again.
    - Tests: `tests/test_skills.py`'s rule checks pass with the skill's rules cut to the commands its bash blocks run, and `test_land_runs_the_train_unattended`.
12. **R12. The docs say how the loop works.** `plugins/factory/README.md`, `docs/REFERENCE.md` and the factory paragraph of `AGENTS.md` describe:
    - `train --run` and `--cancel`;
    - the run lock;
    - the stops, and which ejections the loop makes itself.

    The skill's description stops advising "a session of its own".
13. **R13. `resolve` keeps one rebase onto the base (seed 2026-11-18-44).**
    - The bare `resolve <NNN>` goes. `resolve` takes exactly one of `--onto` and `--continue`.
    - Outside a train, `--onto` takes only the base branch, by name or by its tip. It rebases the change's own commits from their merge base, and returns `current`, `stacked` or `conflict`. The old `clean` state goes.
    - That outside-a-train form writes no train state and opens no landing round. Any other commit outside a train is refused.
    - The rebase, with `.sdlc/last-id` settling itself under `RESOLVE_STEPS`, exists once, in `_rebase_settling()`.

    Tests:
    - `test_resolve_needs_onto_or_continue`;
    - `test_resolve_onto_the_base_outside_a_train`;
    - the register-conflict tests and `test_a_cost_line_written_mid_rebase_goes_into_the_resolved_commit`, rewritten to `--onto main`, still pass.
14. **R14. A resolution leaves the worktree clean (seed 2026-11-18-45).** `resolve --continue` writes `runs/land-resolved` before the rebase continues. It stages that marker and `build/land-<n>.md` (when present) with `RESOLVE_RECORDS`. So a `resolved` result leaves `git status --porcelain` empty, with both files in the rebased commit. On a second conflict, the abort takes the staged marker with it. `_put_back()` already clears a committed marker.
    - Tests: `test_a_resolution_leaves_the_worktree_clean` and `test_a_failed_resolution_leaves_no_marker`.
15. **R15. One test helper drives a train (seed 2026-11-18-46).** `_drive()` and `_land_train()` become one `drive_train(factory, root, capsys, …)` in `tests/train_driver.py`. It takes the `factory` module as an argument, keeps both drivers' options, and neither test file keeps a driver of its own.
    - Test `test_the_train_driver_takes_every_step_a_reading_names`: the driver's steps and `RUN_STEPS` both cover `TRAIN_STEPS`, which lists every `next` that `_train_reading()` can emit.
16. **R16. The reading says why it ejects.** Every `eject` reading carries `cause`:
    - `gate`, from `_train_gate()`;
    - `review`, from a landing round whose `land_verdict()` is `stop`;
    - `refusal`, from `failed` or `_land_readiness()`'s refusal.

    The cause is kept in the change's state with its `fault`. `--eject` copies it into `state["ejections"]`, and the reading's `ejected` list carries it.
    - Test `test_every_ejection_names_its_cause`: drives each of the three cases and checks `cause` on the reading and in `ejected`. It fails if any ejection reading lacks one.

## Design

**The loop is `_train_run()` in `factory.py`, behind `cmd_train(run=True)`.**

Before it starts, it takes the run lock (R6), using `_try_lock()` on `sdlc-factory-train-run.lock` beside `TRAIN_STATE`. It refuses when no train is under way, or when the lock is held and `TRAIN_RUN_ENV` isn't set.

Then it loops:

1. If the cancel file exists, exit `cancel` (R7).
2. Run `factory.py train` as a subprocess, with `TRAIN_RUN_ENV` set, to get a reading.
3. Look up `next` in `RUN_STEPS`. For `eject`, the entry depends on `cause`: `gate` maps to `train --eject <change>`, and any other cause has no entry. A step with no entry is a stop (R4).
4. Run each argv as `[sys.executable, <this script>, …]`. The working directory is the worktree the reading names, or the main checkout for `close` and `--eject`. Each runs in text mode, `encoding="utf-8"`, with no shell. Parse its JSON.
5. Apply R4's rules.

**Why subprocesses.** Each step is then exactly the command 139 pins. Several agents can run at once without sharing `sys.stdout`. The loop itself keeps no state; the next reading decides.

**Output.** Progress goes to stderr, one line a step. The exit JSON carries:
- `landed`, `live`, `moves` and `gates`;
- `ejected`, each with its `reason` and `cause`;
- either `done: true` or `stopped: {next, change, reason, way_on}`.

**The way on, worded by the script:**

| Stop | Way on |
| --- | --- |
| `eject` (review, refusal) | `rerun /sdlc-factory:land to leave <NNN> out and go on, or train --stop to put every change back` |
| `stop` | `train --stop` |
| `accept` | `factory.py accept <NNN>`, then rerun |
| `commit` with `before` | the `before` commands, then rerun |
| `push_failed` | close's own words |
| a refusal | its plain line |
| no progress | `train`'s reading, and `/sdlc-factory:land` by hand |
| `cancel` | rerun, or `train --stop` |

A stop that names a change is also recorded with `_record_land(…, "stop", [reason, way_on])`.

**The cause (R16).**
- In `_train_reading()`, each of the three places that sets `fault` also sets `fault_cause`:
  - step 1's `failed` and `_land_readiness()` refusal set `refusal`;
  - step 3's gate eject sets `gate`;
  - step 4's `land_verdict()` stop sets `review`.
- `done()` passes `cause` through.
- `_train_eject()` appends `{change, reason, cause, first}` to `ejections` and clears `fault_cause` with `fault`.
- A state file from before this change has no `fault_cause`, so it reads as `refusal`, which pauses. An old train never gets an ejection it didn't ask for.

**The gate ejection in the loop (R5).**
- `--eject` puts the change back at its pre-train commit with `git reset --keep`, amends its records and reason in, and prints the undo. The loop logs that undo on stderr and keeps it in the exit JSON.
- The next reading re-stacks the rest and gates the new tip.
- The rule that stops the train when the first change is at fault twice in a row stays a `stop`, so a broken base branch still reaches the person rather than ejecting change after change.
- The loop makes at most one gate ejection per change in the batch, since each ejection removes one live change.

**The stored fix (R9).** `--begin` stores `fix: {change, ask, done}`. When a reading names `close` for that change and `done` is false, the loop runs the three fix commands, sets `done` through `train --fixed <NNN>`, and reads again.

**Agents together (R10).** The loop starts one `Popen` per role and waits for all of them. A `problem` from any of them is a stop, read once all have ended.

**`resolve` (R13, R14).** There are three paths:
- `--onto` in a train, as now.
- `--onto` outside a train: the base branch's tip only. The upstream is `merge-base(HEAD, onto)`, and it returns `current`, `stacked` or `conflict`. It makes no `write_train()` call, no `_fresh_round()` call, and opens no landing round.
- `--continue`: the marker and the reply are staged before `git rebase --continue`.

Both `--onto` paths call `_rebase_settling(root, onto, upstream, env)`. The docstring line saying the bare form is what `fresh` needs goes, since it's wrong.

**The shared driver (R15).** `tests/train_driver.py` is a plain module that pytest's default import mode finds. It holds `drive_train()` and the stand-in writers. It takes `factory` as a parameter and runs `cmd_*` in process. For an `eject`, it runs `--eject` whatever the cause, as the skill did before.

**The skill.** Steps 0 to 2 are unchanged. Step 3 becomes:
1. Run `accept` and `cases` for each change behind the prompt.
2. `Write` the fix line, if any.
3. Run `train --begin … [--fix NNN=R<n>]`.
4. Run `train --run` with the Bash tool's `run_in_background`. The turn then ends.
5. When the harness says the loop has ended, read its JSON. `done` goes to Step 4. A stop gets its reason and way on.

On resume, if the reading names `eject` (a non-gate cause), `stop` or `accept`, the skill runs that one command, then backgrounds `train --run` again. To cancel, the person runs `train --cancel` or kills the task.

Step 4's report says, for each ejection, whether the loop made it on a gate fault or the person resumed past it. The rules shrink to `config`, `sdlc-path`, `land-check` and `train *`. The board is unchanged.

**Edge cases.**
- A kill during `resolve --onto`'s rebase leaves a `resolve` reading with no files: a stop.
- A kill during `train --eject` leaves either the old state, so the reading names the eject again and the loop reruns it, or the ejected state. `_put_back()` with HEAD already at `pre` returns no undo.
- A kill during close is close's own resumable step.
- A kill during an agent session files no reply, and the rerun starts that role afresh.

### Boundaries

- **Always:**
  - take the step the reading names;
  - eject a gate's fault and go on, as the approved question promises;
  - exit at the first stop;
  - hold the run lock.
- **Asks first** (the loop stops, and the person's rerun is the ask): every ejection for a kept change, a used-up mend, an unreadable reply, checks failing as stacked, or a refusal; every train stop; every acceptance check or paid case; every refused push.
- **Never:**
  - commit, push, rebase or reset except through the step commands;
  - run `accept`, `cases` or `--stop`, or `--eject` for a cause but `gate`;
  - retry an agent beyond the mends named;
  - start a second loop;
  - notify beyond the harness and the board;
  - add a config key;
  - move a branch outside a train onto anything but the base.

## Contracts touched

- **"`factory.py agent` is the one place the factory runs `claude`, and `factory.py gate` the one place it runs a host's command."** The loop runs both only as those subcommands.
- **"Landing is the one place it commits, through `sdlc`'s own `ship` and `close`."** The loop commits nothing itself. R14 adds files to the commit that `--continue` already makes.
- **"Branches move only by `resolve --onto`, `land --close`, `--eject` and `--stop`, each printing its undo."** The loop moves a branch through `--eject` only for a gate's fault, and keeps the undo it prints. R13 removes the bare rebase that sat outside the list.
- **"Agents that judge have no Write; only the builder edits; no agent commits."** Unchanged.
- **139's R19, one train.** Unchanged. R6 adds one runner. Its children pass the lock by `TRAIN_RUN_ENV`, in the shape of `sdlc.py`'s `LOCK_HELD_ENV`: the same trust, held by the process that owns the lock.
- **The approved question.** Its words are unchanged and now true unattended: "the change at fault left out with why and the rest landed" is what the loop does on a gate fault. The ejections it doesn't promise pause.
- **Acceptance checks only through `accept`, and paid cases never in rules.** The loop runs neither.
- **Narrow `allowed-tools`, every rule used, no branching in bash.** The rules shrink, and the branching goes into `_train_run()`.
- **One WAIT.** Unchanged.
- **Only the named steps push.** Through `land --close`, which runs `sdlc.py close`, which goes through `_push_plan()`.
- **Windows.** Locks go through `_try_lock()`. Every subprocess call uses `encoding="utf-8"` and no shell. Files are written with `newline="\n"`. There's no `os.kill(pid, 0)`. R8's kill test isn't `portable`. R13, R14 and R16's tests are, where they need no fake `claude`.
- **Nothing public names the agent.** Unchanged: only `Sdlc-*` trailers.
- **No policy invariant moves.** `AGENTS.md` gains a description, not a rule.

## Alternatives rejected

- **Pausing at every ejection (the earlier draft).** The person's yes already approved leaving a gate's fault out and landing the rest. A pause there stops the person where they aren't needed, which is against O6.
- **Running every ejection unattended.** A kept change, a used-up mend or a refusal is a judgement or failure the question never promised to pass over.
- **Telling a gate ejection from the reason's text.** The reason is prose for the person, and a rewording would silently turn a pause into an ejection. `cause` is a field the script sets where it decides.
- **Lifting the lock check for `--eject` with a CLI flag.** A flag anyone can type is no lock. The environment marker, like `LOCK_HELD_ENV`, is set only by the process that holds the lock.
- **A model or sub-agent driving the loop.** It spends tokens and orchestrates landing, which the intent rules out.
- **Running `accept` and `cases` in the loop.** That removes the harness's prompt.
- **In-process steps with threads.** `emit()` shares one stdout.
- **A detached daemon.** It can't notify the session or be cancelled by it.
- **A cancel by a signal mid-step.** A cancel at the step boundary leaves nothing to recover.
- **A `[land] notify` command.** It's a host command run unasked, and a new key.
- **Per-step commands kept in the skill.** Two ways to run the train would drift apart.
- **Dropping the bare `resolve` outright (R13).** The person chose fold, which keeps the register tests short.
- **Amending the reply and marker in at close (R14).** That leaves every stacked worktree dirty.
- **`train --run` as the tests' driver (R15).** A monkeypatch can't reach agents running in subprocesses.

## Verification

```bash
./check.sh
uv run --group dev pytest -q tests/test_train.py tests/test_land.py -n auto
uv run --group dev pytest -q tests/test_factory.py -k "resolve or cost_line" -n auto
uv run --group dev pytest -q tests/test_skills.py -n auto
uv run --group dev pytest -q -m portable
```

Healthy output:
- `check.sh` is green.
- No `def _drive` or `def _land_train` is left under `tests/`.
- `test_train_run_ejects_a_gate_fault_and_lands_the_rest` and `test_every_ejection_names_its_cause` pass.
- `test_skills.py` reports no unused or missing rule in `land/SKILL.md`.
- The `portable` run passes.

By hand, once:
1. In a scratch host with three ready factory changes and a check the middle one breaks, run `/sdlc-factory:land` and say yes. The harness prompts for each `accept` and `cases`. The turn ends with `train --run` in the background.
2. From another terminal, `uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py train` shows `running: true`.
3. The board shows the bisection and the ejection with no session acting. On exit, the session reports `done`, two `Close` commits, and the middle change ejected on the gate with its reason.
4. With a reviewer stood in to keep a change, the run stops at `eject` with cause `review`. A rerun of the skill ejects it and lands the rest.
5. Run `train --cancel` mid-run. It exits after the step in flight.
6. Force a stack conflict. After `--continue`, `git status --porcelain` in that worktree is empty.

