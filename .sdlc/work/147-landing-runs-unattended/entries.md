# 147-landing-runs-unattended — entries

## [2026-11-18-66] [idea] The board shows an unattended landing from the run lock

Left undone by 147-landing-runs-unattended, carried forward when it landed: The board could read the run lock (`sdlc-factory-train-run.lock`) to say a landing is running unattended, rather than inferring it from `runs/land-step.md` alone; the spec left the board unchanged.
See .sdlc/work/147-landing-runs-unattended/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-67] [idea] A Windows test for a killed train run

Left undone by 147-landing-runs-unattended, carried forward when it landed: `test_a_killed_train_run_resumes` kills a process group, so it doesn't run on Windows; a Windows kill test would need `CREATE_NEW_PROCESS_GROUP` and `taskkill /T`.
See .sdlc/work/147-landing-runs-unattended/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-68] [nit] `RUN_STEPS["eject"]` is looked up, but `RUN_EJECTS` and the cause check already guard it.

Raised by the code review of 147-landing-runs-unattended, round 1: plugins/factory/scripts/factory.py:6291: `RUN_STEPS["eject"]` is looked up, but `RUN_EJECTS` and the cause check already guard it. The `RUN_STOPS` tuple (line 6163) looks unused; remove it or use it for the `accept` and `stop` branches.

Theme: refactor
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 147-landing-runs-unattended (correctness)

## [2026-11-18-69] [nit] after a SIGKILL of the loop, an orphaned agent subprocess can still be running when a rerun starts, because the lock descriptor isn't inherited.

Raised by the code review of 147-landing-runs-unattended, round 1: plugins/factory/scripts/factory.py:6330: after a SIGKILL of the loop, an orphaned agent subprocess can still be running when a rerun starts, because the lock descriptor isn't inherited. The only guard is that the same step named twice stops the loop. A comment saying so, or a test, would help.

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: M
Value: low
Raised by: 147-landing-runs-unattended (correctness)

## [2026-11-18-70] [nit] R4's stops for a non-zero step exit, an agent `problem`, `resolve` with no conflicted files and a `land.moves` stop have no test of their own.

Raised by the test review of 147-landing-runs-unattended, round 1: tests/test_train.py: R4's stops for a non-zero step exit, an agent `problem`, `resolve` with no conflicted files and a `land.moves` stop have no test of their own. The spec lists four R4 tests and all four exist, so the gap is only in what R4's list promises.

Theme: tests
Paths: tests/test_train.py
Cost: M
Value: low
Raised by: 147-landing-runs-unattended (correctness)

## [2026-11-18-71] [nit] the kill test waits up to 120 s (600 polls of 0.2 s) for the stand-in reviewer to start, which is slow on a loaded machine but not flaky.

Raised by the test review of 147-landing-runs-unattended, round 1: tests/test_train.py:1468: the kill test waits up to 120 s (600 polls of 0.2 s) for the stand-in reviewer to start, which is slow on a loaded machine but not flaky.

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 147-landing-runs-unattended (correctness)
