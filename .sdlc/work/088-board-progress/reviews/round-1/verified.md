Both claims hold: the state is only colour plus `title` (line 213), and the progressbar sits inside a `<button>` (line 217).

- KEPT: ux: C1: scripts/board.html:213: step state is carried only by colour and a `title` tooltip, so done and to-do look the same to a screen reader or touch user, and the paused state has only a dashed border
- KEPT: ux: C2: scripts/board.html:217: the `role="progressbar"` is inside the card's `<button>`, so assistive tech drops it; the meta line already gives the same figures, so the bar can be `aria-hidden`

## Notes
I read `scripts/board.html` and the step-building code in `scripts/board.py`, and I ran nothing. The line numbers, CSS and JS show both defects. The proposed wording in C1 is only a suggestion, so the builder can choose the exact text.
