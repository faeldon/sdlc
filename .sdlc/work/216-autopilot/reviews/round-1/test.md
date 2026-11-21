VERDICT: PASS

Every requirement from R1 to R28 maps to a named test. The tests I read can fail, and the gate record is green.

## Notes

- **Coverage:** I confirmed that each test the plan names exists in `tests/`. Spot-checked tests: R4, R3, R16, R18, R21, R23 and R27. Their assertions are specific:
  - R4 greps the scripts for any `("auto", "person")` pair and checks `BY_VALUES`.
  - R16 asserts that nothing starts after the step in flight, that the cancel file is cleared, and that a rerun doesn't reopen a seed.
  - R18 asserts that `upgrade` is held and never run.
  - R21 asserts that `accept` runs before the train and that `cases` and `run-cases` never run.
  - R27 asserts that a spent budget opens one seed and starts no train.
- **Gate:** `build/round-1.gate.md` reads `GATE: PASS` with exit 0 on `./check.sh`. Its record lists a count of 3931 passed and 29 skipped.
- **Named run:** `uv run --group dev pytest tests/test_autopilot.py -q` gave 47 passed.
- **Known limit:** The end-to-end test and the loop tests drive the loop in process, with `run_step` stood in for. No test runs the loop's real subprocesses with a fake `claude`. The builder reported this, and it matches how the train's own tests work. I don't count it as a finding.
- **R6, R7, R24, R26:** The builder wrote the code before these tests, so they never ran red. Reading them, each asserts on specific behaviour and would fail if the code were removed.
- **checks.md:** Both checks are plain `grep` and `test -f` commands that don't touch the tree.
  - The first greps for the `autopilot.py` entry in `[review] sensitive` in `.sdlc/config.toml`. I expect it to pass now and fail if the entry were removed.
  - The second looks for the skill file and its one WAIT heading. I expect the same.
- NIT: tests/test_autopilot.py:263: many `# fmt: skip` pragmas keep dense literals unformatted {style S low}
