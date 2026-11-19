VERDICT: PASS

The kept change from last round was made. `_finite()` now catches `OverflowError`, so a JSON integer over about 308 digits is reported as `line 1's value isn't a number` and no longer crashes `host_rows`. The new case is in `test_output_that_isnt_rows_passes_through_with_its_reason`, a 400-digit value.

## Notes
- The gate's record, `build/round-2.gate.md`, is green (`GATE: PASS`, exit 0).
- I ran `tests/test_indicators.py` in the foreground, which is not a whole-suite run: 67 passed.
- The overflow case can fail. Without the `try/except` in `_finite`, `math.isfinite` raises `OverflowError` and the case errors.
- No `checks.md` section was needed for this rework.
