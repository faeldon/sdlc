I've resolved the conflict in `tests/test_board.py`, and the full gate passes (2486 tests). I edited only that file and ran no git command.

The conflict was at the end of the file, where both sides added a new section after `test_the_focus_trap_skips_a_hidden_node`. The two sections don't depend on each other, so the fix was to keep both:

- **From the base branch:** the landing-track section (133), unchanged. That covers `_landing_at()`, `LANDS`, `LABELS` and the ten tests from `test_a_landing_card_shows_its_landing_track` through `test_a_stopped_landing_drops_the_ready_look`.
- **From this change:** the drawer section (138), unchanged and placed after the base's. That covers `_DRAWER_RUN`, `_drawer()`, `test_a_stale_response_never_paints_over_the_newer_file` and `test_an_empty_file_says_so`.

No conflict markers are left, and no name is defined in both sections. Both of this change's drawer tests ran and passed. The one skip in the selection below is a base test at line 1200 that skips itself on purpose, not one of this change's.

## Evidence

$ grep -n '^<<<<<<<\|^=======$\|^>>>>>>>' tests/test_board.py
(no output)

$ uv run --group dev pytest tests/test_board.py -q -n auto
183 passed, 14 skipped in 6.29s
exit: 0

$ uv run --group dev pytest tests/test_board.py -q -rs -k "stale_response or empty_file_says or landing"
SKIPPED [1] tests/test_board.py:1200: landing stopped and landing are two readings of one record
43 passed, 1 skipped, 153 deselected in 9.65s
exit: 0

$ ./check.sh
All checks passed!
280 files already formatted
2486 passed, 14 skipped in 81.07s (0:01:21)
✔ Validation passed
exit: 0
