- KEPT: ux: C1: scripts/board.html:47: `.col.needs-you { order: -1 }` is visual only. `render()` (lines 287-294) builds the columns in stage order, so at phone width Tab and screen-reader order put Needs you last, after every other column's cards.

## Notes
- I ran no tests. I read `scripts/board.html` (the CSS at line 47 and `render()`), `tests/test_board.py` around line 891, and the change's `intent.md`, `notes.md` and `decisions.md`.
- The defect is real. `render()` maps `COLUMNS` in stage order with no phone-width handling, and the CSS `order` changes only the visual order.
- The intent's Outcome says "Moves O6: the board reads the same on a phone, by keyboard and with a screen reader", so this is a missed outcome, not a matter of taste. The builder's own `notes.md` and the code and UI reviewers' D3 and D4 (in `decisions.md`) also record the gap.
- The intent's Approach names "a media-query `order`" alone, but the Approach is the builder's plan and the Outcome is the requirement. The two conflict, and I resolved it in favour of the Outcome.
- There is no `spec.md` in this change folder, so I judged against `intent.md`. The "spec asks for a focus order" in the change's wording is really the intent's O6.
- Rework the test at tests/test_board.py:891 along with the fix, as the change says. It currently pins CSS-only `order: -1`.
- If the rework keeps the CSS `order` rule alongside a DOM reorder, it is harmless. If both apply, Needs you is first either way.
