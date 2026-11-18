VERDICT: PASS

## Notes
- The fix does what the person asked. `timed_rows` and `land_sinces` moved to `scripts/factory_records.py` with their helpers (`_run_time`, `_json_rows`, `RUN_TIME_FORMAT`). `closing._lead_marks` now builds its two paths from `factory_records.LAND_TIMES` and `COSTS`, so `closing.py` spells no record file name any more.
- The `git show` calls stay in `closing.py`. That is consistent with the module's contract: `factory_records.py` is pure and runs no subprocess.
- Coverage is kept:
  - The 162 pin test, `test_close_reads_the_run_rows_the_factory_writes`, now calls the moved functions with the same inputs and expected values. That test reads real rows written by `factory.record_cost` and `_record_land`, so it fails if the parsing or the row format drifts.
  - `tests/test_archive.py:2335` still runs `_lead_marks` end to end.
  - `tests/test_modules.py` requires the new names in `factory_records.py` and forbids the old `_timed_rows` and `_land_sinces` elsewhere.
- The gate record `build/land-2.gate.md` shows GATE: PASS. Its output tail, which I read, stops mid-run, so I didn't see the count there. The builder's evidence gives 3052 passed, 28 skipped.
- I ran only named tests: `pytest tests/test_modules.py tests/test_archive.py -k "lead or timed or land_sinces or closing or no_other or record"`, 27 passed.
- No `checks.md` was added in this round.
