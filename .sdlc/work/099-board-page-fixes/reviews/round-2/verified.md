- KEPT: ux: C1: scripts/board.html:293: the render key is `JSON.stringify([NARROW.matches, st.changes])`. It includes `touched_ago` in whole seconds (board.py:161), so the key changes on every poll and `replaceChildren` rebuilds every card, which drops card focus. `#board` still has `aria-live="polite"` (line 137), and `#status` is the better place for it. No test pins the key to what is shown.

## Notes
- I ran nothing. I read `scripts/board.html` lines 160–400 and `scripts/board.py:161`, and checked `git status`.
- The "Settled" text in the prompt concerns the narrow-width DOM order. It is not one of this round's changes, and the code already has `columnOrder()` with a re-render on the `NARROW` change, so I gave it no line.
- Any change that sets `touched` makes the key unstable. A key built from `ago(c.touched_ago)` would fix that, and it still changes when the minute label changes.
