VERDICT: PASS

I found no Critical or Required problems. I walked R1–R16 against the diff and the tests and read the gate record, but I ran no tests of my own.

- **R3/R4:** `_run_plan()` and `RUN_STEPS` cover the listed steps. Only `train --eject` for cause `gate` is automatic. `accept`, `cases` and `train --stop` never run. Every other ejection cause stops the loop.
- **R6/R7:** the run lock is held on an open descriptor, so a killed loop releases it. A stale cancel file is cleared when a loop starts. `--cancel` is checked only between steps.
- **R4 `moved`:** `land --close` reports `moved` with exit 0, so the loop correctly keeps going.
- **R13/R14:** `_rebase_settling()` is now the single place the rebase runs. `resolve --continue` writes the marker first and stages it with `RESOLVE_RECORDS` and `build/land-<n>.md`.
- **R11/R12:** the land skill's description and the build skill's "session of its own" line are updated. No other doc I could find still says it.

## Notes
- NIT: plugins/factory/scripts/factory.py:6291: `RUN_STEPS["eject"]` is looked up, but `RUN_EJECTS` and the cause check already guard it. The `RUN_STOPS` tuple (line 6163) looks unused; remove it or use it for the `accept` and `stop` branches. {refactor S low}
- NIT: plugins/factory/scripts/factory.py:6330: after a SIGKILL of the loop, an orphaned agent subprocess can still be running when a rerun starts, because the lock descriptor isn't inherited. The only guard is that the same step named twice stops the loop. A comment saying so, or a test, would help. {robustness M low}
- Done well:
  - Each step runs as a subprocess of this script, so the step is the command the tests pin.
  - The exit JSON reports ejections with their causes.
  - `RUN_STEPS` is pinned against `TRAIN_STEPS`.
  - The tests cover each stop.
- Gate: `build/round-1.gate.md` is green (`./check.sh`). I ran nothing myself.
