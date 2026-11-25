VERDICT: PASS

I checked R1–R29 against the diff, and R30 against the gate record. I found no Critical or Required problems.

## Notes
- The gate record `build/round-1.gate.md` says `GATE: PASS` on `./check.sh`. I did not rerun it, and I ran no named tests.
- The code edits match the Design section exactly:
  - R1: the `uncarried()` branch for a SETTLED default the ledger never ticked sits before the "no `- CONFIRM:` line" fallback.
  - R2: the two `except` clauses in `closing.py` narrowed to `(OSError, ValueError)`, with the docstrings updated.
  - R4: `from_host` now needs the marker at the start of the body.
  - R6: `--preview` with any clause flag is refused before `cmd_ship_preview` runs.
  - R7: the autopilot skill's goal-quoting text changed, and its bash blocks did not.
- `scripts/retro.py` has a change the spec's Design section doesn't list: `_read_hosts` now skips a listed path that a `!` line excludes. R15 needs it, because it asserts `read` is 1 when one of two hosts is excluded. It is small, and its docstring says what it does.
- Done well:
  - Tests are tied to the code they pin. R27 goes through `cmd_restart` instead of setting `start` by hand. R11 runs both copies of the writer against one lock. R10 adds a keyword-only fixture. R9 asserts the fixture before reading `verdicts`.
- I did not check R3 and R5 (retired, no test) or the full `entries.md` accounting of the 31 nit ids. I only counted the lines in `entries.md` (32).
