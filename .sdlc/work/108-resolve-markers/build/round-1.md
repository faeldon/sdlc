Bug 51 is fixed: both resolves now refuse a file only for a conflict marker on a line of its own. The full gate passes (2174 passed, 9 skipped). Nothing is committed; HEAD is still `204da52`. This report is the same as the last one, with every result rerun and shown below.

This is Tier 1 and touches two scripts plus their tests, so there is no `plan.md`.

## Slices built

**The fix.** `scripts/sdlc.py` and `plugins/factory/scripts/factory.py` each now have the same line-anchored `CONFLICT_MARKER_RE`, `^(?:<{7} |={7}$|>{7} )` with `re.M`, in place of the old substring check. It matches seven less-than signs and a space, seven equals signs alone, or seven greater-than signs and a space, each at the start of a line. Both resolve continue steps use it. The factory's copy is commented as a copy of `sdlc.py`'s, pinned by a test.

**Tests added or changed**
- **New: `test_land.py::test_a_conflict_marker_is_matched_only_as_a_whole_line`.**
  - It pins the factory's pattern to `sdlc.py`'s.
  - In both scripts these pass: each script's own source, a register entry that quotes the run mid-line, and an underline of eight equals signs.
  - In both scripts a real marker of each of the three kinds is refused.
- **`test_resolve.py::test_a_conflict_with_the_base_is_resolved_shipped_and_closed`:** its inbox resolution now quotes the run mid-line, which proves `sdlc.py resolve --continue` goes on through it.
- **`test_land.py::test_a_batch_lands_in_order_and_a_conflict_is_resolved_reviewed_and_closed`:** its README resolution now quotes the run mid-line, which proves the same for the factory's resolve. Its earlier step, where unresolved markers are refused, still holds.

To show red, I copied HEAD's code into a scratch folder with the new tests and ran them there; all three fail. In the worktree with the fix, both test files pass.

Nothing is left in `notes.md`.

- DECISION: [default] Should a line of exactly seven equals signs count as a marker, as the intent says, even though a Markdown heading underlined to exactly that length would be refused? Options: keep it; match only the less-than and greater-than kinds. Going ahead with keeping it: the intent says so, and an underline of exactly that length is rare in a conflicted file.

## Evidence

$ cd /tmp/red108 && uv run --group dev pytest tests/test_land.py tests/test_resolve.py -q -p no:cacheprovider -k 'whole_line or a_batch_lands or resolved_shipped'
FAILED tests/test_land.py::test_a_batch_lands_in_order_and_a_conflict_is_resolved_reviewed_and_closed
FAILED tests/test_land.py::test_a_conflict_marker_is_matched_only_as_a_whole_line
FAILED tests/test_resolve.py::test_a_conflict_with_the_base_is_resolved_shipped_and_closed
3 failed, 35 deselected in 4.44s
exit: 1

$ uv run --group dev pytest tests/test_land.py tests/test_resolve.py -q
38 passed in 50.69s
exit: 0

$ ./check.sh
All checks passed!
248 files already formatted
2174 passed, 9 skipped in 56.82s
✔ Validation passed
✔ Validation passed
exit: 0
