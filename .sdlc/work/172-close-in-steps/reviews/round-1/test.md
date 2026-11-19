VERDICT: PASS

The tests cover R1–R9. R4's characterization test and R7's new test pass. R8's assertion and R9's test are new or extended, and each can fail without its fix. No requirement is left without a test that would fail without it.

## Notes
- **Gate:** `build/round-1.gate.md` is green: `3075 passed, 28 skipped`. I re-ran three named tests in the foreground, and 9 passed. They were `test_close_output_is_unchanged` (5 scenarios), `test_close_is_a_sequence_of_named_steps` and `test_the_rerun_ceiling_keeps_its_last_cent` (3 cases).
- **R1, R2:** the AST test fails on a nested `def` in `cmd_close`, on a body over 40 lines, or on any function in `closing.py` over 100 lines.
- **R3:** the new names are in `CLOSING_NAMES`. They are checked through the existing `test_close_push_and_the_lock_live_in_closing`.
- **R4:** the test pins five scenarios against a recorded fixture, `tests/fixtures/close-output.json`. Each pins the report text with key order, the exit code, the newest commit and the tree. A moved key or a renamed step would fail it.
- **R7:** it asserts `opened_at() > CLOSED_AT`, so it exercises the "parses but later" branch and not the malformed one. It also checks that no `errors` key appears. The plan says it was seen failing when the branch it pins was broken.
- **R8:** the new `measure.errors` assertion is exact, and the `closing.py` diff shows `errors` is only set when non-empty.
- **R9:** the cases are 0.65 → `4.35`, 0.30000000000000004 → `4.7` and 0.305 → `4.69`. The plan records why the last two differ from the spec. The rounding-down case is covered.
- **R5, R3:** the `tests/` edits go beyond what R5 lists. I read each edit and found nothing wrong.
  - `test_only_the_named_steps_push` now follows the push into `_step_push`. It still catches a planted `_push(` caller: it uses a word-boundary match and checks that only `_run_close_steps` calls `_step_push`.
  - `_close_preview` is now the place that must call `_push_plan(`.
  - The plan flags these departures as "raised as a default".
- **Acceptance checks:** there is no `checks.md`. R13 and R14 are docs and are reviewed by reading.
- **Test commands:** I ran only the named tests above. I did not run the whole suite.
