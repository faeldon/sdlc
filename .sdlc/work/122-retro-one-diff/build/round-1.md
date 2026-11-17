A retrospective now runs one `git diff -U0` per change instead of two, and its report comes out the same. The full gate passes (2249 passed, 13 skipped) and everything is left uncommitted.

This is a Tier 1 change touching two files, so I wrote no `plan.md`. There is no `notes.md` and no `checks.md`: the new test stays in the suite.

**Slice: share the diff** (one slice, test first)
- **Red:** I added `test_a_retrospective_reads_each_change_s_diff_once` to `tests/test_retro.py`, run once for `retro` and once for `retro_report`. It sets up two closed changes, wraps `sdlc._git` and counts the `-U0` diffs for each change. It failed for the expected reason: each change's diff ran twice.
- **Green:** in `scripts/retro.py`, a new `_diffs()` reads each change's `_added_diff()` once into a map keyed by change name.
  - `retro()` and `retro_report()` each build that map once and pass it to `_rework()` and `_spend()`.
  - `_rework()` gets the map as a new `diffs` argument, so its blame step no longer runs the diff itself.
  - `_spend()` takes the map in place of `bases` and stops calling `_added_diff()`.
  - Both docstrings now mention the map.
- **Output unchanged:** the other 120 retro tests pass unchanged.
  - I also ran `retro_report()` on this repo's own history (48 changes in the window) before and after the change. The two reports are identical, and the `-U0` count dropped from 96 to 48.
  - I didn't compare the full `retro()` output that way, because it runs this repo's `retro.evidence` command. Rework and spend, the only parts this change touches, both appear in the report.

The fixed comparison date in that script was today's, so the output matched the live view.

The intent also notes that `retro_report()` calls `_change_rows()` for each change, which `retro()` does too. That is outside this change's stated outcome, so I left it alone.

## Evidence

```
$ uv run --group dev pytest tests/test_retro.py -q -k diff_once     # before the code change
E       AssertionError: Counter({'8060d0b': 2, '7292a3c': 2})
E       AssertionError: Counter({'fc8646f': 2, '81500ee': 2})
2 failed, 120 deselected in 2.58s
exit: 1

$ uv run --group dev python -I /tmp/snap122/snap.py "$PWD" /tmp/snap122/before.md   # before
48 changes; 96 -U0 diffs in retro_report
exit: 0

$ uv run --group dev pytest tests/test_retro.py -q                  # after
122 passed in 39.25s
exit: 0

$ uv run --group dev python -I /tmp/snap122/snap.py "$PWD" /tmp/snap122/after.md    # after
48 changes; 48 -U0 diffs in retro_report
exit: 0

$ diff <(sed '$d' before.md) <(sed '$d' after.md)      # in /tmp/snap122: the two reports, minus the count line
exit: 0

$ ./check.sh
All checks passed!
245 files already formatted
2249 passed, 13 skipped in 188.32s (0:03:08)
✔ Validation passed
exit: 0
```
