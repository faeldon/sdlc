VERDICT: PASS

The end-to-end path from the spec's Verification section does what the spec says. `change` is not a name the spec uses, so I took "the end-to-end path" to mean `sdlc.py retro` run on this repo, plus the named tests.

## Notes
- **`checks.md`:** none exists for this change, so there is nothing to read or run.
- **`by_way`:** it has all three ways (`factory`, `manual`, `unknown`) in every part (`changes`, `lead`, `throughput`, `cost`, `escapes`).
- **Hand-built cost:** `manual.cost.usd` is `{n: 0, median: null}` with `built by hand: 1` under `missing_because`. `manual.cost.tokens.n` is 1.
- **Null rates:** `unknown.escapes.rate` is null, not 0, as the spec requires.
- **Throughput row:** the last row's `ways` and `classes` each sum to `total` (29, 29, 29).
- **Escapes:** `rate.window.by_way` sums to 5, the same as `rate.window.escapes`.
- **Tests:** the 22 selected retro tests pass. They cover by_way, retired grouped seeds, setup's record and work class. The gate record `build/round-1.gate.md` reads `GATE: PASS`; I did not run the full suite.
- **Not run:**
  - I did not render the report with `retro_report()` or view the *By way of building* table (R8). Only its test, `test_the_report_compares_the_ways_of_building`, ran.
  - I did not run `skills/retro` or `status`.
  - I did not run the `grep "vanished"` doc check.
  - The unit tests cover these paths.
- **Slow run:** `retro` on this repo took longer than 120 seconds and moved to the background. It finished with exit 0.

## Evidence
$ uv run --quiet --script scripts/sdlc.py retro > /tmp/r176.json; python3 -I -c '…print by_way, last throughput row, sums, rate.window'
tail: by_way changes factory 28 / manual 1 / unknown 0; manual usd `{n:0, median:null, missing_because:{"built by hand":1}}`; manual tokens n 1; throughput row `ways` and `classes` both 29 = total 29; rate.window `{escapes:5, changes:29, rate:0.17, by_way:{factory 4/28, manual 1/1, unknown 0/0 rate null}}`
exit: 0

$ uv run --group dev pytest tests/test_retro.py -q -n auto -k "by_way or way or retired or setup_s_record or work_class or milestone or compares"
tail: 22 passed in 2.72s
exit: 0

$ head -5 .sdlc/work/176-by-way-of-building/build/round-1.gate.md
tail: GATE: PASS
exit: 0
