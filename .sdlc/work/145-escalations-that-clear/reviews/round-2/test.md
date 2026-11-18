VERDICT: PASS

The round-2 rework made the one kept change. `test_nothing_rewrites_decision_md` is in tests/test_land.py:2791 rather than tests/test_factory.py, and the build moved the plan's R10 line to match.

- **What it covers:** it writes a `decision.md` with a `gate` line and a `look` line. It then runs `decisions`, `ask`, `sdlc.py gate`, `land-check` and the board's state in turn. After each one it asserts the bytes are unchanged, with the step's name as the failure message. That is the single test R10 asked for.
- **Can it fail:** the builder's Evidence shows it failing, with `AssertionError: ask`, when `ask` was made to append a line to `decision.md`, and passing again after the revert.
- **Gate:** `build/round-2.gate.md` is `GATE: PASS`. The builder's `./check.sh` run reported 2750 passed and 28 skipped.

## Notes

- **Not run by me:** I ran no test and read the gate record's header only. The test count comes from the builder's Evidence.
- **Checks:** the change has no `checks.md`, and nothing in the spec needs one.
- **Settled:** I raised nothing new on code that round 1 already passed.
- **Nits:** none.
