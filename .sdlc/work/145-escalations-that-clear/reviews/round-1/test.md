VERDICT: CHANGES

The gate record `build/round-1.gate.md` is `GATE: PASS`, with 2749 passed and 28 skipped. Most requirements have a test that would fail without them. R10 has a gap.

- CHANGE: tests/test_factory.py: R10 asks for one test that runs `ask`, `decisions`, `sdlc.py gate`, `land-check` and the board's state on an escalated change and finds `decision.md`'s bytes unchanged. The plan names it `test_nothing_rewrites_decision_md`, and it doesn't exist. Partial byte checks are spread around:
  - `test_a_green_hand_gate_clears_a_gate_reason_until_an_edit` in tests/test_board.py checks `gate` and the board's state.
  - `test_land_check_shows_how_each_reason_was_cleared` in tests/test_land.py checks `decisions` and `land-check`.
  - The `decisions` byte check at tests/test_factory.py:842 only covers the old `D<n>` forms.

  No test runs `ask` on an escalated change and checks the bytes, and none holds a `look` or `gate` decision through all five commands. Add the one test, on a decision holding a `D<n>`, a `look` and a `gate` line, and assert the bytes are equal after each command.

## Notes

- **Gate and test count:** I read the gate record only and ran no test. It shows 2749 passed, 28 skipped, and `ruff` and `claude plugin validate --strict` both passed.
- **R12:** `test_decide_asks_each_look_and_runs_nothing_for_a_gate` is a wording test, as the plan says.
- **R17:** No test file in the diff named `PRECEDENCE`/`BOTH` pairs. The board test file's 444-line change probably holds them, but I didn't confirm each pair.
- **Checks:** The change has no `checks.md`, so there are no acceptance checks to judge. Nothing in the spec needs one.
- **Well covered:**
  - R2–R6, R8, R9, R11, R13–R16, R19–R23, R26 and R27 each have a named test.
  - R25's new line is asserted at tests/test_board.py:1216 and :1424.
  - R7's no-gate-sample check is `test_a_hand_gate_record_is_no_land_gate_sample`.
  - R20's `land-ship/2` is asserted at tests/test_board.py:2671 and :2675.
  - R24's pin is `test_the_land_record_readers_are_pinned_copies`.
- **Nits:** none.
