The one kept change is fixed: on a phone, Needs you now comes first on the page itself, not just on screen, so Tab and screen readers reach it first. The full gate passes, 2001 tests. As before, the tests only read the page's source; nothing runs the new ordering in a browser.

**The kept change:**
- **ux C1, phone focus order:** fixed. In `scripts/board.html`, `render()` now builds the columns through a small `columnOrder()` function. At or below 760px it puts Needs you first; at desktop width it keeps stage order.
  - It checks the same 760px width the CSS uses, and redraws the board when the window crosses that width.
  - I removed the CSS `order: -1` rule, so screen order and Tab order now come from one place and can't drift apart.
  - This settles D2–D4 in `decisions.md`. Nothing new needs deciding.

**Test changed:** `test_needs_you_comes_first_at_phone_width_and_nowhere_else` now checks that:
- the script uses the same width as the CSS;
- Needs you comes first only when the screen is narrow, and stage order holds otherwise;
- `render()` uses `columnOrder()` and never `COLUMNS` directly;
- crossing the width triggers a redraw;
- no CSS `order` remains.

It failed before the fix, on the width check, as expected. One existing test failed during my first gate run because it greps the script for the word "style", and my comment said "stylesheet". I reworded the comment to "CSS"; the test is unchanged.

**`notes.md`:** the phone-order item is ticked off. Still open: no browser test exercises the drawer's focus trap, because that needs a dependency the gate doesn't have.

There's no `plan.md` for this Tier 1 change, and I raised no new decisions this round.

## Evidence

$ uv run --group dev pytest -q tests/test_board.py -k phone_width   # before the page changed
E       AssertionError: the same width as the CSS
1 failed, 50 deselected in 0.18s
exit: 1

$ ./check.sh   # first run, comment still said "stylesheet"
All checks passed!
214 files already formatted
1 failed, 2000 passed in 96.64s (0:01:36)
exit: 1

$ ./check.sh
All checks passed!
214 files already formatted
2001 passed in 94.15s (0:01:34)
✔ Validation passed
✔ Validation passed
exit: 0
