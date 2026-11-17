VERDICT: CHANGES

- CHANGE: scripts/board.html:213: a step's state (done, current, paused, to do) is carried only by colour and a `title` tooltip. Done and to-do pills differ only in green versus grey. Screen readers and touch users don't get the tooltip, so they can't tell how far the run has got. Put the state in the pill's text or a visually hidden label, for example a "✓" on done steps and "now:" or "waiting:" on the current one. The paused (waiting on the person) state needs its own wording too, because the dashed red border is the only thing marking it.
- CHANGE: scripts/board.html:217: the `role="progressbar"` sits inside the card's `<button>`. A button's children are presentational, so assistive tech drops the role and its label, and the elapsed-versus-typical figure is lost. The meta line already says it in text (`18m · ~40m typical · estimate`), so make the bar `aria-hidden` and rely on that line. Also make the text line always present when the bar is, which it already is.

## Notes

I read both screenshots, `intent.md`, `board.html` (the CSS and `progressRow`/`card`) and `board.py`'s `_progress`. I did not read the spec or `decisions.md`, so I judged the path against the intent's Outcome.

- **Screenshots:** the 088 card appears with no step track. No `runs/step.md` existed at capture, so the card shows nothing about progress. That fits "absent rather than invented", but I could not see the track, the bar or the plan hint rendered. I judged those from the code. At 390px the track uses `flex-wrap`, so it should wrap without trouble. The phone screenshot shows only the Plan column, so I couldn't check the factory card at that width.
- **Other states:** a run with no history shows `N so far` alone and the bar is dropped, which is clear. A stopped run gets no track, and the existing "stopped:" flag covers that.
- **Smaller findings:**
  - During a fix, the label "fixing" lands on the `gate` slot. Check that the track still shows a separate rework slot, so "fixing" and "rework" don't read as two different things.
  - `plan: X of Y files touched` is hard-coded to `None` in `_progress` (line 413). Check that the plan hint is wired elsewhere, or the stated outcome has no way to appear.
  - "R2 of 3" has no unit. "round 2 of 3" would be clearer.
  - Step labels are lowercase internal names (`gate`, `verify`). They are acceptable for this audience.
- **Done well:** the estimate is honestly labelled ("estimate (N runs)") and capped. The bar is left out when there is no history, and the page builds every node with `textContent`.
