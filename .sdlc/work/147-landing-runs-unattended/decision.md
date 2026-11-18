DECISION: READY

**Why.** All three round-1 reviewers (code, test, behaviour) returned `VERDICT: PASS` and found nothing Critical, High or Required. The gate is green: `./check.sh` passed 2683 tests with 18 skipped, the portable run passed 508, and the test reviewer found a named test for each of R1–R16. The plan explains its two departures from the spec's design, the main one replacing `train --fixed` with a `next: fix` step that stays inside R3's command list. The person decided both calls in `decisions.md` (R1, R2), and the build follows them. Nothing in the rounds suggests the spec was wrong.

**Open items**
- None open. What remains is four NITs, none with a CHANGE:
  - code: `RUN_STOPS` looks unused, and the `RUN_STEPS["eject"]` lookup duplicates a guard.
  - code: an agent orphaned after a SIGKILL of the loop has no guard but the no-progress rule; it needs a comment or a test.
  - test: R4's other stops (a non-zero step, an agent `problem`, `resolve` with no conflicted files, a `land.moves` stop) have no test of their own.
  - test: the kill test can wait up to 120 s.

**Decisions to confirm**
- No blocking decisions are unticked, and no defaults are open.

**For the person at ship**
1. In `factory.py`, check `_run_loop()` and `_run_plan()`. The loop must eject on its own only when `cause == "gate"` (`RUN_EJECTS`). It must never run `accept`, `cases` or `train --stop`. Check the no-progress rule too, since it is the only guard against a step left running when a killed loop is rerun.
2. Check the run lock and `TRAIN_RUN_ENV` in `cmd_train()`. Without the marker, `--begin`, `--eject`, `--stop` and a second `--run` must refuse while a loop runs.
3. Check that `_train_reading()` sets `fault_cause` at each of its three places. A state file from before this change has none, and must read as `refusal`, which pauses.
4. Check the removal of the bare `resolve <NNN>`. Outside a train, `--onto` must take only the base branch, write no train state and open no landing round.
5. In the `land/SKILL.md` rewrite, `accept` and `cases` must stay behind the harness's prompt, outside `allowed-tools`.

- IMPACT: minor — a factory host can now land a train unattended with `train --run`, and stop it with `train --cancel`. The bare `factory.py resolve <NNN>` form is gone, but no skill or script ran it.

**Each undone item's disposition**
- UNDONE: The board could read the run lock (`sdlc-factory-train-run.lock`) to say a landing is running unattended, rather than inferring it from `runs/land-step.md` alone; the spec left the board unchanged. → seed: The board shows an unattended landing from the run lock
- UNDONE: `test_a_killed_train_run_resumes` kills a process group, so it doesn't run on Windows; a Windows kill test would need `CREATE_NEW_PROCESS_GROUP` and `taskkill /T`. → seed: A Windows test for a killed train run
