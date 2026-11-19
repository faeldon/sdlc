All three conflicted files are resolved with no markers left, and `tests/test_retro.py` passes in full (178 passed). Both sides' work is kept in each file.

**`scripts/retro.py`**
- **Helpers:** 168's `_pct` and `_value_text` and 170's `_coverage_line`, `UNDERNEATH_NAMES`, `_underneath_text` and `_coverage_lines` are all kept. They don't overlap.
- **`render_report` signature:** both sides had changed it. It is now `render_report(template, process, spend=None, value=None, metrics=None)`. `value` keeps its place from 168, so the existing calls still work, and 170's `metrics` is added after it. The docstring covers both.
- **Report order:** `{{window}}` is the window sentence, then 170's *Coverage* lines (with *What changed underneath*), then 168's three value sentences. The `if value:` append from 168 and the `_coverage_lines(...)` call from 170 both stay.
- **`retro_report`:** it builds `value = value_band(...)` and `metrics = metrics_summary(...)`, then calls `render_report(template, process, spend, value, metrics)`.

**`tests/test_retro.py`:** 168's "Value band" tests and 170's "trust band" tests sit one after the other with a blank-line gap. Neither is edited.

**`docs/REFERENCE.md`:** 168's paragraph on work mix, time to users and follow-through is followed by 170's paragraphs on coverage, underneath and the factory window. Neither is edited.

I noticed one thing and left it. Two `tests/test_retro.py` tests call `retro_report` or `render_report`. Under the 168 and 170 order, 169's own changes weren't in this conflict, so I didn't check how its report lines would sit beside these two.

## Evidence

$ grep -n '^<<<<<<<\|^=======\|^>>>>>>>' docs/REFERENCE.md scripts/retro.py tests/test_retro.py
exit: 1

$ uv run --group dev ruff format --check scripts/retro.py tests/test_retro.py
2 files already formatted
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_retro.py
178 passed in 31.08s
exit: 0
