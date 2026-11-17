The bug both reviewers found was real, and it's fixed. A card holding keyboard focus made the board's next rebuild throw, so the board showed "the board isn't answering" and still lost focus. The gate is green again (2091 passed).

**What was wrong:** `render()` declared its own `const open`, the count for the totals line. That hid the drawer's `open`, which the new focus check `if (held && !open)` reads earlier in the same function, before the local is set. So whenever a card had focus, a rebuild threw a `ReferenceError`. That skipped putting focus back, the totals line and the status update, and `poll()` fell into its error branch. My round-1 test only matched the source text, so it couldn't see this.

**KEPT, code (`scripts/board.html`):** I renamed the local to `openCount` and used it in `#totals`, so `open` now means the drawer again. I also made `test_a_rebuild_puts_focus_back` catch the bug: it now fails if `render()` declares any `const`, `let` or `var open`, and checks the drawer's `let open = null;` is still declared at the top level of the script. I watched it fail on the old code ("render() shadows `open`") and pass after the rename. I took the reviewer's first option, the source check, rather than running the page in node, because the suite's Windows CI may not have node.

**KEPT, ux:** the same rename fixes it. To check the behaviour itself, I ran `render()` in node against a small stand-in for the browser page. With a card focused and a change that forces a rebuild, the old code throws `ReferenceError: Cannot access 'open' before initialization`. The fixed code rebuilds, puts focus back on the same card (`002-x`) and writes the totals line. That script was a one-off in `/tmp` and isn't part of the suite.

`plan.md` doesn't need updating, since the fix is within what it already describes, and I added nothing to `notes.md`.

No decisions raised.

## Evidence

$ uv run --group dev pytest -q tests/test_board.py -k rebuild_puts_focus   (before the rename)
E       AssertionError: render() shadows `open`
1 failed, 123 deselected in 0.19s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py -k rebuild_puts_focus   (after the rename)
1 passed, 123 deselected in 0.04s
exit: 0

$ node /tmp/h107/run.js   (fixed page)
rebuilt: true focus on: 002-x totals: 2 open · 0 by the factory
exit: 0

$ node /tmp/h107/run.js   (the same page with the old `const open` put back)
ReferenceError: Cannot access 'open' before initialization
exit: 1

$ ./check.sh
All checks passed!
2091 passed, 9 skipped in 45.37s
✔ Validation passed
exit: 0
