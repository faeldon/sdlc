R5's test now passes, and so does the full gate (3052 passed, 28 skipped). I ran no git command and left everything uncommitted.

What changed:
- **`scripts/closing.py`:** 162's two parsers, `_timed_rows` and `_land_sinces`, moved to `scripts/factory_records.py`, along with the three things only they used: `RUN_TIME_FORMAT`, `_run_time` and `_json_rows`. They are now `timed_rows` and `land_sinces`, and their bodies are unchanged.
- **`_lead_marks` stays in `closing.py`** with its own `git show` calls, since close is still the only place those git reads run. It now builds the two file paths from the module's `LAND_TIMES` and `COSTS` and parses through `sdlc.factory_records`. With no file name spelled in `closing.py` any more, R5's test passes.
- **`tests/test_archive.py`:** the two calls in 162's pin test now go to `sdlc.factory_records.timed_rows`/`land_sinces`, with the same inputs and expected values.
- **`tests/test_modules.py`:** I added `timed_rows` and `land_sinces` to the names the module must define. The old names `_timed_rows` and `_land_sinces` are now on the list no other file may define. This goes slightly beyond the minimal fix, but it keeps R3's boundary true.

I didn't update `plan.md` for this; it doesn't mention 162's readers.

## Evidence

$ uv run --group dev ruff check scripts tests --output-format concise
All checks passed!
exit: 0

$ uv run --group dev pytest -q -n 4 tests/test_modules.py tests/test_archive.py tests/test_metrics.py
364 passed in 33.83s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 163 > /tmp/b163/check2.log 2>&1; echo "exit: $?"; grep -E "[0-9]+ passed|failed|All checks" /tmp/b163/check2.log | tail -3
All checks passed!
3052 passed, 28 skipped in 125.09s (0:02:05)
exit: 0
