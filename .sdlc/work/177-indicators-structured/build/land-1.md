I resolved all three conflict hunks in `scripts/retro.py`, and the retro tests pass.

**What I kept from each side**
- **`render_report` signature:** I kept 174's `cost: dict | None = None` and 177's `indicators: list[dict] | None = None`, in that order. `cost` comes first because 174 added it first.
- **`render_report` docstring:** I merged both. It keeps 174's `cost` coverage-lines wording and 177's `indicators` sentence ("with none `{{indicators}}` says no indicators are set").
- **`retro_report`:** it keeps 174's `cost = _cost(home, changes, dropped)` and 177's `host = _indicator_rows(...)`. It then calls `render_report(template, process, spend, value, metrics, cost, host)`.
- **Already in the file and unchanged:** the `_coverage_lines(process, spend, metrics, cost)` call and the `"indicators": _indicators_text(indicators)` entry.
- **179:** it didn't conflict, so I touched nothing for it.

**Left short:** nothing.

**Noticed and left alone:** nothing.

## Evidence

$ grep -c '^<<<<<<<\|^>>>>>>>' scripts/retro.py
0
exit: 0

$ uv run --group dev pytest -q tests/test_retro.py -n auto
189 passed in 36.59s
exit: 0

$ uv run --group dev ruff check scripts/retro.py
All checks passed!
exit: 0
