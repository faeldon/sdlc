All three files are merged and the conflict markers are gone. `tests/test_modules.py` passes (50 passed). I did not run the full suite or any 233 or 227 tests beyond that file.

**`plugins/factory/scripts/factory.py`**
- 227's side already moves `record_closes(...)` (with the refusal on `OSError`) earlier in `agent`, ahead of the session record. I kept that placement.
- From 233 I kept only the `elif task == "mend": step_before = _record_mend(...)` branch after the `LAND_TASK_STEP` check.
- I dropped 233's older copy of the `record_closes` block, because it would have run twice.

**`scripts/board.py`**
- I kept 233's `entry["mending"]` reading, which reads the step record only when the card is stopped.
- I kept 227's park comment, which mentions the `[park] deadline` cut (229), and left the `parked` reading as it was.

**`tests/test_modules.py`**
- I kept both additions to the record names: `capped_park` for 229 and `"ROLE_RE", "mending"` for 233.
- `CONSUMER_NAMES` now ends `"UI_DEFAULTS", "_park_deadline_at", "mend_running"`, so it has both sides' names.

I noticed nothing to flag.

## Evidence

$ grep -n -E '^(<<<<<<<|=======|>>>>>>>)' plugins/factory/scripts/factory.py scripts/board.py tests/test_modules.py
exit: 1

$ uv run --quiet --group dev pytest -q tests/test_modules.py
50 passed in 3.06s
exit: 0
