VERDICT: PASS

Neither round-2 screenshot shows the new progress track, so I judged it from the code and the styling around it. Card 088 in the 1280px shot has the "R1" round tag, chips and a "next:" line, but no step pills, bar or time line. The board had no `runs/step.md` to read for that run.

Both points kept from last round are fixed in `scripts/board.html`:
- **State in text:** `STEP_WORDS` (line 212) puts "✓ ", "now: " and "waiting on you: " in the pill text. Done and to-do pills now differ by more than colour, and the paused state has its own wording.
- **Bar and meta line:** the bar is `aria-hidden` (line 221), and the meta line under it carries the elapsed and typical figures in text.

## Notes
- I read `index-1280x800.png` and `index-390x844.png`, and `scripts/board.html` lines 14–24, 80–99 and 205–230.
- The 390px shot has only hand-made cards in the Plan column, so the wrapping of the step track at phone width is unverified. `.track` uses `flex-wrap: wrap`, so it should hold.
- The new `.step`, `.bar` and `.progress` styles use the existing tokens (`--pass-bg`, `--accent`, `--stop`, `--chip`, `--muted`). No colour is hard-coded, and the dark theme's token values are already defined.
- The longer "waiting on you: " pill text is the likeliest thing to crowd a narrow card. Check it once a paused run is on screen.
- Done well: the step pills follow the existing `.chip` sizing, and the elapsed-versus-typical bar is labelled "estimate" in the text.
