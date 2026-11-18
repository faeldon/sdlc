VERDICT: PASS

The change touches the board only in `scripts/board.py` (a Python string and a "resolving" label), and no CSS. The screenshots show the board page as it stands, so they don't show the new landing "resolve" step itself.

## Notes
- I read `index-1280x800.png` and `index-390x844.png`. I read neither the repo's styling docs nor the gate record, since no stylesheet changed.
- At 1280px the six columns line up. Headings, count badges, card chips and the red "needs you" text read clearly, and the red text also carries words, so nothing depends on colour alone.
- At 390px the board collapses to a single column. Cards fit the width with no sideways scroll, and the chips wrap cleanly. The 008 card is cut off at the bottom of the capture, which is the screenshot's limit and not an overflow.
- The long `next:` lines in monospace wrap inside the cards at both widths.
- No screenshot shows a card in the new "resolving" landing state, so I couldn't check how its label looks. The change adds only text to the existing chips, so I don't expect a problem.
- The change does reuse the existing chip, step and "needs you" styles (e.g. the "now:" chip) and adds no one-off classes, which is what the surrounding board does.
