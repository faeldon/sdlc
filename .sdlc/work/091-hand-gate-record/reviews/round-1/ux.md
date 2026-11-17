VERDICT: PASS

No required changes. The one UI addition, a hand-built card's `gate green` / `gate red` badge, reads clearly and is reachable by keyboard.

## Notes
- **Read:** the 1280 and 390 screenshots, `intent.md`, and the gate-related parts of `scripts/board.html` and `scripts/board.py`. I did not read `spec.md`, `decisions.md` or the Python tests.
- **Not visible in the screenshots:** every card is a factory card, so no by-hand card with a gate badge appears. I judged that state from `board.html` lines 253–267 and the `next_action` text in `board.py` (line 598). The factory cards, which are unchanged, render fine at both widths with no overflow.
- **Hand-built card, green gate:** the badge reads `gate green` in words as well as colour. It shows only when the record is current, so a stale record claims nothing. The card moves to Test and says what to do next.
- **Hand-built card, red gate:** the badge reads `gate red`. The next line is "the gate is red: read build/gate.md, fix it, then sdlc.py gate NNN", which names the file and the rerun command.
- **Keyboard and phone:** cards are real `button` elements and columns carry `aria-label`s. The badges are plain spans, so they stack in the 390px layout.
- **Smaller findings:**
  - Green and red differ by colour and text. The `gate-green` and `gate-red` classes are text-coloured only. That is acceptable, since the text carries the meaning.
  - The `gate green` badge appears on every card, including factory cards. The factory card shows the gate step in its round track instead, so check that a factory card never also gets the badge.
- **Done well:** the red state names its own recovery command, and a record counts only while it matches the current build. A card therefore never claims "gate green" for code it didn't judge.
