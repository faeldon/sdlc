VERDICT: CHANGES

- CHANGE: [correctness] scripts/indicators.py:~513: `math.isfinite(value)` raises `OverflowError` for a JSON integer over about 308 digits. I ran `host_rows('{"name":"a","value":' + '9'*400 + '}')` and it crashed. The error propagates out of `_indicator_rows`, so one odd host line fails the whole `retro` and `retro-commit`. R2 says anything that isn't rows must pass through. Fix: wrap the finiteness check in `try/except OverflowError` and return `(None, f"line {n}'s value isn't a number")`, or reject an int that `float()` can't convert. Add a case to `test_output_that_isnt_rows_passes_through_with_its_reason`.

## Notes
- NIT: scripts/indicators.py:~560: `_cells` strips each cell, so a name with leading or trailing spaces never matches its `last` (it is silently null), and a unit of literal `—` reads back as `""`. Either reject such names and units in `host_rows`, or document the limit. {robustness S low}
- Done well: the parsing is pure and sits in `indicators.py`. `cell()`, `number()` and `signed()` are shared by the writer and the reader. The report never holds raw output or stderr. `TEMPLATE_READS` and `setup.json` were updated in the same change.
- Context: the AGENTS.md *Retrospectives* paragraph is updated. The docs and skill edits read as true.
- I ran no tests. I read the gate record and it is PASS. I ran one ad-hoc Python call to confirm the overflow.
