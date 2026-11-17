VERDICT: PASS

## Notes

- Requirements 1 and 2 are met. Both scripts' checks now match only whole-line markers (`<{7} `, `={7}$`, `>{7} `). The factory's copy is pinned to `sdlc.py`'s by `test_a_conflict_marker_is_matched_only_as_a_whole_line`. The test also runs both sources and a quoted mid-line run through the pattern. Real markers of each kind are still refused.
- Requirement 3 is met. The mid-line run in `test_land.py` and `test_resolve.py` exercises the new behaviour in the land and resolve paths.
- Test gaps, optional: the new test checks the pattern directly, not each script's `cmd_resolve` path. Spec wording says "runs each script's check", so the two read slightly differently. The existing `test_land` and `test_resolve` cases do go through the real `cmd_resolve`, which covers the gap in practice.
- Edge cases, optional, not blocking: a CRLF separator line `=======\r\n` is not matched by `={7}$`. The opener on the same conflict is still caught, so a real conflict is still refused. A marker with no label (`<<<<<<<` with nothing after) is not matched. Git always writes a label on a merge, so this doesn't arise in practice.
- Known trade-off: a Markdown setext underline of exactly seven `=` is refused. This is already open as D1 and D2 in `decisions.md`, with defaults. The two lines are duplicates and say the same thing, so one could be struck when the person decides.
- Done well: the fix is small and in the right place in each script. It carries a comment explaining why the rule is line-anchored, and the factory copy is pinned by a test, as the contract requires.

Tests and commands run, all read-only:
- `uv run --group dev pytest -q tests/test_land.py tests/test_resolve.py`: 38 passed.
- `uv run --group dev pytest -q tests/test_defaults.py tests/test_nothing_local.py tests/test_windows.py`: 160 passed.
- `ruff check` and `ruff format --check` on the four changed files: clean.
- A probe of the regex on edge cases (CRLF, unlabelled markers, setext underlines, mid-line quoting) to check the findings above.
