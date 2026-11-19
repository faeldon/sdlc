VERDICT: PASS

The kept change is fixed. `host_rows` on a 400-digit JSON integer now returns `(None, "line 1's value isn't a number")` instead of raising `OverflowError`. The fix is `_finite()` in `scripts/indicators.py`, which catches the `OverflowError` and returns False. A normal row (`value: 3`) still parses to a row.

## Notes
- `checks.md` doesn't exist for this change, so there are no acceptance checks to read.
- The spec names no command-line path for this fix. I ran the closest one, calling `host_rows` directly with the input from the finding.
- The gate record `build/round-2.gate.md` shows `GATE: PASS`.
- I added no new test. Line 460 of `tests/test_indicators.py` already covers the 400-digit case, and `tests/test_indicators.py` passes (67 tests).

## Evidence
$ cat .sdlc/work/177-indicators-structured/build/round-2.gate.md | head -3
GATE: PASS
(the file begins with `GATE: PASS`; its tail shows `✔ Validation passed`)

$ python3 -I - (load scripts/indicators.py, call host_rows on a 400-digit value and on `value: 3`)
(None, "line 1's value isn't a number")
([{'name': 'a', 'unit': '', 'value': 3, 'extra': {}}], None)
exit: 0

$ uv run --group dev pytest tests/test_indicators.py -q
67 passed in 0.04s
exit: 0

$ grep -n "isfinite\|OverflowError" scripts/indicators.py
417:    return seconds if seconds is not None and math.isfinite(seconds) and seconds > 0 else None
492:        return math.isfinite(value)
493:    except OverflowError:
exit: 0

$ grep -n '"9" \* 400' tests/test_indicators.py
460:        ('{"name": "a", "value": ' + "9" * 400 + "}\n", "line 1's value isn't a number"),
exit: 0

$ ls .sdlc/work/177-indicators-structured/checks.md
ls: .sdlc/work/177-indicators-structured/checks.md: No such file or directory
exit: 1
