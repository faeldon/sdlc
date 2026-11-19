- KEPT: code: C1: scripts/indicators.py:514: `math.isfinite(value)` raises `OverflowError` for an int of about 309 or more digits, which `json.loads` accepts, so one odd host line fails the whole `retro`. The finiteness check needs guarding, and a test case needs adding.

## Notes
- I ran `math.isfinite(int('9'*400))` in Python 3.12 and it raised `OverflowError`.
- `json.loads('9'*400)` parses without error. Python's int-digit limit is 4300, so such a line reaches line 514.
- I did not run `host_rows` itself or any repo test, and I did not read the `_indicator_rows` caller. The claim that the error escapes `_indicator_rows` rests on the report and on the absence of a `try` at line 514.
- `_parsed` (line 572) and `_seconds` (line 417) are different paths. `_parsed` calls `int(text)` on report text, so it could hit the same overflow, but that is not part of this change.
