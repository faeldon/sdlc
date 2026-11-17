VERDICT: PASS

## Notes

- **Correctness.** Each change's `git diff -U0` now runs once in `_diffs()`, and `_rework()` and `_spend()` both read from that dict. The output path is unchanged: `_added_diff()` is the same function the old `_spend()` called, and `_rework()` only skipped changes with no base, which it still does. The new test in `tests/test_retro.py` covers both `retro()` and `retro_report()`.
- **Outcome wording.** The intent's Outcome asks the test to count "the git calls". The test counts only `diff -U0` calls per change, which is what the intent's failure condition names. That reading is acceptable.
- **Naming drift.** The intent's Affected section names `_change_diff()`, but the code calls the helper `_diffs()`. The intent is the only doc in the folder (there is no `spec.md`), so this is a stale name, not a defect.
- **Memory.** `_diffs()` holds the full `-U0` text of every change in the window at once. Before, each diff was built, used and dropped one change at a time. A long window with large diffs now costs more memory. That is a cost trade-off, not a correctness problem, so I'm not raising it as a CHANGE.
- **Evidence the test pins the change.** On HEAD, `_rework()` (`scripts/retro.py:831`) and `_added_diff()` (`:966`, called from `_spend()`) each run `diff -U0` for a change with a base. So the old code makes two such calls per change and the new assertion would fail on it. I reasoned this from the code and did not run the test against HEAD.
- **Done well:** the change is small, keeps `indicators.py` pure, leaves the read-only contract intact, and the docstrings on `_rework()` and `_spend()` say where `diffs` comes from.

Checks run: `uv run --group dev pytest -q tests/test_retro.py` (122 passed), `ruff check` on both changed files (passed), and `ruff format --check` on both (already formatted). I did not run the full `./check.sh` gate.
