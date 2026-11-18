VERDICT: PASS

## Notes
- The move matches what the person asked for. `timed_rows` and `land_sinces`, with their helpers `RUN_TIME_FORMAT`, `_run_time` and `_json_rows`, are now in `scripts/factory_records.py`. `_lead_marks` stays in `closing.py` with its own `git show` calls, and builds both paths from `records.LAND_TIMES` and `records.COSTS`, so `closing.py` spells no file name. The parsers are pure, so `factory_records.py` still has no subprocess call and no import of `sdlc.py`.
- `tests/test_modules.py` now requires `timed_rows` and `land_sinces` in `factory_records.py` and bars the old private names from every other file, which keeps R3's boundary true. 162's pin test in `tests/test_archive.py` still uses the same inputs and expected values, now through `sdlc.factory_records`.
- I read `build/land-2.md` and the code. I ran no tests. The builder reports a full gate of 3052 passed and 28 skipped, and I did not check that record against `build/land-2.gate.md`.
- NIT: `scripts/closing.py:326`: `_lead_marks` reaches `factory_records` as `records` in one branch and as `sdlc.factory_records` in the other. Using the local alias in both would read more evenly. {style S low}
