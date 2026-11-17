Confirmed: line 324 reads `open`, and line 330 declares `const open` in the same function. That puts line 324 in the temporal dead zone, so it throws when `held` is set.

- KEPT: code: C1: scripts/board.html:324: `render()` reads `open` before its own `const open` at line 330, so it throws a ReferenceError when a card has focus. Rename the local, and make the test catch shadowing.
- KEPT: ux: C2: scripts/board.html:324: the same TDZ ReferenceError. It skips the totals and status update, and `poll`'s catch then reports "the board isn't answering". Rename the local count.

## Notes
- I read `scripts/board.html` lines 315–335 and grepped for `open`. I ran no tests.
- C1 and C2 are the same defect. The test-strengthening request in C1 is an extra that the rename alone doesn't cover.
- `held` is not shown in the range I read. I assumed it is truthy when a card has focus, per the change descriptions.
