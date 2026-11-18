I resolved `tests/test_train.py`, but the gate is red: 2830 passed, 1 failed. The failure is a real interaction between 147 and what is already on main, and the fix is in `plugins/factory/scripts/factory.py`, which this task didn't allow me to edit.

**The resolution.** The file had no conflict markers left when I opened it. The combined diff shows a merge of both sides, and I checked it against each side and 147's spec.
- **From main (145 R22):** `test_a_waiting_change_records_what_it_waits_on` and its `_waits()` helper stay as they are. 147's R15 replaced the file's own `_drive()` with the shared `drive_train(factory, root, capsys, …)` in `tests/train_driver.py`, so the test's three `_drive(...)` calls now call `drive_train(factory, ...)`. Only those three lines differ from either side.
- **From 147:** everything else in the file is 147's, unchanged: the shared driver import (R15), `test_every_ejection_names_its_cause` (R16), `test_a_resolution_leaves_the_worktree_clean` (R14) and its updates to the existing tests.
- No `_drive` is left anywhere in `tests/`. `tests/test_train.py` and `tests/test_land.py` run 121 passed, 1 failed.

**The failure.** `test_a_resolution_leaves_the_worktree_clean` (147 R14) finds `?? .sdlc/work/002-second/runs/land-times.jsonl` after `resolve --continue`. Main added that file in 145: `write_land_step()` appends a row to `runs/land-times.jsonl` whenever the step changes. 147's `RESOLVE_RECORDS` (`COSTS, LAND_STEP, runs/builder.sessions`) was written before that file existed, so `--continue` stages `land-step.md` but not the timing file the same write produces. The worktree is left dirty, which is exactly what R14 forbids.

I didn't loosen the test, because that would hide a real R14 breach. I also left `factory.py` alone, since the task limited me to the conflicted file.

- DECISION: [blocking] Let the landing add `LAND_TIMES` to `RESOLVE_RECORDS` in `plugins/factory/scripts/factory.py`, outside the conflicted files? Recommend yes.
  - OPTION: add it — a one-line change, `RESOLVE_RECORDS = (COSTS, LAND_STEP, LAND_TIMES, Path("runs") / "builder.sessions")` (`LAND_TIMES` is defined earlier in the file). The timing rows go into the rebased commit and R14 holds; the fix touches a file outside the conflict.
  - OPTION: make the test ignore `runs/land-times.jsonl` — stays within the conflicted file, but every resolution would leave an uncommitted file behind, breaking R14 in practice.
  - OPTION: eject 147 and rework it — the fix goes through a normal review round, at the cost of a full round for one line.
  - WHY: R14 says the worktree is left clean, and this file is a record of the same kind as `land-step.md`, written by the same call.

## Evidence

$ git status --short (filtered to non-added entries)
UU tests/test_train.py
exit: 0

$ grep -n '<<<<<<<\|>>>>>>>' tests/test_train.py
(no output)
exit: 1

$ grep -n '_drive\b\|def drive_train\|import.*drive_train\|drive_train =' tests/test_train.py tests/*.py
tests/test_train.py:27:from train_driver import DRIVER_STEPS, asked, drive_train, fake_claude, verdict, verified
tests/test_land.py:19:from train_driver import drive_train
tests/train_driver.py:60:def drive_train(
exit: 0

$ uv run --group dev pytest tests/test_train.py tests/test_land.py -q -n auto
FAILED tests/test_train.py::test_a_resolution_leaves_the_worktree_clean - Ass...
1 failed, 121 passed in 62.23s (0:01:02)
exit: 1

$ ./check.sh
FAILED tests/test_train.py::test_a_resolution_leaves_the_worktree_clean - Ass...
1 failed, 2830 passed, 28 skipped in 115.00s (0:01:55)
exit: 1

$ uv run --group dev pytest tests/test_train.py::test_a_resolution_leaves_the_worktree_clean -q
E       AssertionError: nothing left uncommitted
E       assert '?? .sdlc/wor...d-times.jsonl' == ''
E         + ?? .sdlc/work/002-second/runs/land-times.jsonl
exit: 1

$ grep -n 'RESOLVE_RECORDS' plugins/factory/scripts/factory.py
6774:RESOLVE_RECORDS = (COSTS, LAND_STEP, Path("runs") / "builder.sessions")
6828:    records (`RESOLVE_RECORDS`), and continues, so the rebased commit holds them and the worktree is
6942:    for record in (*RESOLVE_RECORDS, marker.relative_to(folder), Path("build") / f"land-{n}.md"):
exit: 0

The `pytest` run on `test_train.py` and `test_land.py` printed `exit: 0` in my shell because `$?` read the `tail` in the pipe. The run had a failure, so its real exit was 1, as shown.
