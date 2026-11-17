VERDICT: PASS

The kept change is code-only, and the board's look doesn't move with it. Both screenshots still render the stop card the way the earlier round accepted, so nothing visual is in question here.

- **Wiring (`scripts/board.py:352-356`):** `_stopped(folder)` now returns `sdlc.factory_stop(folder)`. Its docstring says so, and the old "a test pins the two" wording is gone.
- **Regexes:** `STOPPED_RE`, `NEXT_RE` and `PROBLEM_RE` are no longer in `board.py`. A grep for `re.compile` shows only the board's own regexes (`STEP_RE`, `ROUND_RE` and the rest), none of them stop-record copies. `STOPPED` stays because `_progress()` reads it, as the build note says.
- **Screenshots:** `index-390x844.png` shows card 006 with `stopped: build/round-1.md has no ## Evidence section` and `needs you: stopped: mend`, with its `next:` block wrapping inside the card. `index-1280x800.png` shows the same card in NEEDS YOU, with the same wording. Both match what `factory_stop()` returns, so the wording on screen comes from the one reader now.

## Notes

- Read both screenshots: `index-1280x800.png` and `index-390x844.png`. I didn't run the server or a browser, so the review is from the images and the code only.
- At 390px the cards stack in one column with no horizontal scroll. The monospace `next:` blocks wrap inside their cards.
- At 1280px the NEEDS YOU column runs past the bottom of the 800px frame (card 007 is cut off). That's normal for a scrolling column, not a layout break.
- The stop line is red and labelled `needs you:`, so it doesn't depend on colour alone.
- `build/round-2.md` says the full gate passes with 2201 tests. I didn't re-run it.
