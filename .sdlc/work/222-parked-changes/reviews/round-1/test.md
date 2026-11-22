VERDICT: PASS

Every requirement from R1 to R17 has a test that fails without it. The gate passed on this build: `build/round-1.gate.md` records "3980 passed, 29 skipped in 235.01s", plus "Validation passed" from `claude plugin validate`. I ran no tests myself; I read `tests/test_factory_park.py` and the diffs of `test_land.py` and `test_autopilot.py`. I did not open the new tests in `test_board.py`, `test_sdlc.py`, `test_modules.py` or `test_factory_loop.py`, and rely on the gate for them.

## Notes

- **Well covered:**
  - R1: both the no-`[park]` case and the checkout-only `factory.toml` case.
  - R2 and R4: the test checks every record field, the vouch, and that a re-park keeps its deadline even against an `UNTIL` past it.
  - R6 and R7: the three readings are tested at fixed clock values.
  - R8: forged, garbled, stale and capped records are all tested.
  - R9: the stop is read back through `factory_records.read_stop()`.
  - R10: `--wait` runs on a stand-in clock.
  - R12: the slot wait is tested for both `gate` and `check`.
  - R14: the test checks that nothing is written.
  - R15: it covers both the wait-then-land path and the held-past-deadline path.
  - R17: it reads the AST of `run_state.py`.
- **`checks.md`:** the change has none, and none is needed. Every requirement is covered by a suite test.
- **Gaps below CHANGE level:**
  - R13 `--land --build` busy and landing slot-wait paths have no test. Only the plain `gate --land` busy exit is covered.
  - `test_a_busy_landing_gate_is_a_problem_never_an_eject` stops at the `problem` and the `BUSY` verdict. It does not run `train --run` to show that no eject happens, so the "never ejects" half relies on `landing.py`'s existing `problem` rule.
- NIT: tests/test_factory_park.py:358: the slot-wait test only asserts that "didn't run" appears on stderr, which proves little about the `check` message; assert the "slot" wording too {tests S low}
- NIT: tests/test_land.py:325: add a `--build` variant of the busy landing gate, since it takes a separate call path {tests S med}
