I fixed the one KEPT change. An oversized integer in an indicator's output is now rejected as not a number instead of crashing `retro`. The named tests pass; I didn't rerun the whole suite.

**KEPT change from round 1**
- code [correctness] `scripts/indicators.py`, `math.isfinite` overflow: I added the reviewer's case to `test_output_that_isnt_rows_passes_through_with_its_reason`, a `value` of 400 nines. It failed first, as expected. A new helper, `_finite()`, wraps `math.isfinite` in `try/except OverflowError` and returns `False` on overflow. So that line becomes `(None, "line 1's value isn't a number")`, and the output passes through as text, as R2 says. `report_rows()`'s value reader had the same crash path, so it now uses `_finite()` too.

**Tests run:** `tests/test_indicators.py` (67 passed, one more than last round) and the indicator tests in `tests/test_retro.py` (7 passed). `ruff check` and `ruff format --check` are clean on the two changed files.

`plan.md` is unchanged, and nothing new went into `notes.md`. I raised no decisions this round.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_indicators.py   (the new case, before the fix)
1 failed, 66 passed in 0.12s
exit: 1

$ uv run --group dev pytest -q tests/test_indicators.py
67 passed in 0.05s
exit: 0

$ uv run --group dev ruff check scripts/indicators.py tests/test_indicators.py
All checks passed!
exit: 0

$ uv run --group dev ruff format --check scripts/indicators.py tests/test_indicators.py
2 files already formatted
exit: 0

$ uv run --group dev pytest -q tests/test_retro.py -k "indicator"
7 passed, 177 deselected in 4.24s
exit: 0
