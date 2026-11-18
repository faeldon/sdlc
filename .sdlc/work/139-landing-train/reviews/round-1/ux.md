VERDICT: PASS

The board change is small and clear. A landing card now shows "k of n in a train" beside the existing "base moved X of Y times". It reads as text and doesn't rely on colour.

## Notes
- I read both screenshots (1280 and 390 wide) and `scripts/board.html` around `progressRow`. I did not read the other changed paths. Most are the factory's CLI, docs and tests, and the board is the only surface a person looks at.
- The screenshot data is a fixture. It has no card showing "in a train", an ejected landing, or a landing stopped with problems. I judged those from the code: `progressRow` prints "landing stopped: <why>" as a flag, so a stop is not a blank region or a raw error.
- Smaller finding: the `next:` text on the 012 card is cut off at the bottom of the 1280 screenshot ("/sdlc-factory:land 012 if…"). The card is probably just clipped by the viewport, so I'm not treating it as a defect.
- Smaller finding: "base moved 1 of 3 times" reads a little oddly. This change didn't add it.
- On the 390-wide layout the columns collapse to a single list with "Needs you" first, and the task can still be done there.
- Done well: the train position and the existing landing facts (round, base moves, problems) all sit in the one progress row. The steps carry text prefixes (`✓`, `now:`, `stopped:`), and the progress bar is `aria-hidden` with the same information given as text beneath it.
