The fixture doesn't show a parked card, so the change isn't visible in the screenshots.

VERDICT: PASS

## Notes
- I read `index-1280x800.png` and `index-390x844.png`. Both show the board fixture. Neither shows a parked card or a parked-deadline need, so the changed park code in `scripts/board.py` (lines 281–285 and 439–441) isn't visible in them. This is PASS with a note, not a visual sign-off on the park change.
- Desktop, 1280px: the columns line up, and card spacing and the red "needs you" styling are consistent. Nothing overflows or clips.
- Phone, 390px: the board collapses to one column. Long `next:` command text wraps inside the cards, and nothing scrolls sideways.
- Red text on white and the green and blue chips read clearly. Status is also carried by words ("needs you", "gate red"), not by colour alone.
- Check by eye that a parked card reuses the existing chip or label classes, since `board.py` builds its nodes with `textContent`.
- The board does well to keep the state wording (`parked`, `needs you`) in step with the shared `sdlc.park_line`, so the board and `status` describe a park the same way.
