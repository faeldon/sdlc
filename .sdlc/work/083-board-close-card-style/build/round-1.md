Cards in **Ready to close** now look like cards in every other column. The cause was the drawer's × button sharing the `close` class with that column's cards. I renamed the button's class to `d-close` and added a test that stops a column key from clashing like that again. The full gate passes (1851 tests). Everything is left uncommitted for `/sdlc:ship`.

**What changed** (Tier 1, two files, so no `plan.md`):
- **Fix**, in `scripts/board.html`: the drawer's × button now has the class `d-close` instead of `close`, which matches the drawer's other `d-*` names, and the stylesheet's `.close` rule is now `.d-close`. Ready to close cards keep `card close`, so `.col.close` still works and the × button's style is the same as before. No script on the page selects by `.close`. The `column` values in `/state.json`, the `textContent`-only rule and the phone-width layout are all unchanged.
- **Test**, in `tests/test_board.py`: `test_no_column_key_is_a_class_the_page_styles_on_its_own` (marked `portable`). It reads the `COLUMNS` keys and the stylesheet from `board.html`, and fails if any key is styled as a class without `.col` or `.card` in the same compound selector. Before the fix it failed for the reason I expected, reporting `['.close']`. It now passes, and it proves the third bullet of the intent's Outcome.

The intent's open question (which class to rename) is answered by its own Approach, so I followed that. I haven't struck the question from `intent.md`. Nothing went into `notes.md`, and no other file changed.

DECISION lines: none.

## Evidence

```
$ uv run --group dev pytest -q tests/test_board.py -k no_column_key     # before the fix
>       assert not clashes, clashes
E       AssertionError: ['.close']
1 failed, 14 deselected in 0.29s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py                      # after the fix
15 passed in 8.07s
exit: 0

$ ./check.sh
All checks passed!
187 files already formatted
1851 passed in 296.24s (0:04:56)
✔ Validation passed
exit: 0
```
