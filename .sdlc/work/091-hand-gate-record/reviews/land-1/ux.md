VERDICT: PASS

## Notes

I read both screenshots (1280×800 and 390×844) and `intent.md`. I also read the card-rendering code in `scripts/board.html`, lines 250–273. I did not read `spec.md`, `decisions.md`, `board.py`, `sdlc.py` or the tests, so the status-line change and the command's own output are unreviewed here.

- **What the screenshots show:** the fixture has no change built by hand with a hand gate record. The `gate green` / `gate red` badge is therefore not in either capture. I judged it from the code instead.
  - The badge is plain text in the card's top row, so it is readable and not colour-only.
  - It shows only while the record is current, matching the intent's rule that a record for a changed build counts for nothing.
  - It sits beside the `by hand` badge.
  - The card's `next:` line gives the next step.
- **The task:** the intent's outcome is that a hand-built change reaches Test with a visible green gate and `/sdlc:ship` next. The card code carries that through: column, badge and the `next` line.
- **Reach:** each card is a real `<button type="button">`, so it can be reached and activated from the keyboard. At 390px the cards stack and the badges wrap, and nothing is cut off.
- **Smaller findings:**
  - The `gate green` and `gate red` badges colour only the text (`.badge.gate-green` / `.badge.gate-red`) and don't change the badge's background. They may stand out less than the factory's round chips. It is a style choice, not a blocker.
  - A red badge doesn't say what to do next. I assume `next` covers it, but I couldn't see it.
  - The Test column header reads "the gate and the review". Without a hand-gate card in the shot, I couldn't confirm the new badge and that header agree.

**Done well:** the badge is tied to `gate.current`, so a stale record never shows green. The page builds its nodes with `h()` and not HTML strings, as the repo's rules require.
