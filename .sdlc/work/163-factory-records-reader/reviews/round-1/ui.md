VERDICT: PASS

The change touches no styling. It moves the factory-records reader into `factory_records.py`. The board renders as before.

## Notes
- I read both screenshots, `index-1280x800.png` and `index-390x844.png`. I did not open `board.py` or the gate record.
- At 1280px the six columns line up, and the cards, chips and red "needs you" text are readable.
- At 390px the board collapses to a single column with no sideways overflow or clipping. The header wraps cleanly.
- The "needs you" cards are easy to find. They have a red accent border, a bold red need line, and a section heading in the same red.
- Progress chips use a tick, a label and a colour together, so state does not depend on colour alone.
- The 390px shot cuts off at card 008 (Import drafts). The rest of the page is outside what I could judge.
