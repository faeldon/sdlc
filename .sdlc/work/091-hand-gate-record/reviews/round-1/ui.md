VERDICT: PASS

The screenshots don't show the change itself. Every card on the board is a factory card, so the "by hand" card with a "gate green" or "gate red" badge never appears. I could only check the badge in the source.

## Notes
- I read `index-1280x800.png` and `index-390x844.png`. I also read the badge code in `scripts/board.html`, at lines 71–72 and 256–258.
- At 1280px the columns line up and nothing overflows. The 391 card's rows wrap cleanly.
- At 390px the board stacks into one column and nothing scrolls sideways.
- The new badges use `var(--accent)` and `var(--stop)` and sit in the existing `.badge` class, so they follow the board's tokens and don't hard-code colours.
- The badge text, "gate green" or "gate red", says the result in words, so colour is not the only signal.
- I couldn't check contrast for the badge colours, because no screenshot shows one.
- The change does well to reuse the existing badge component rather than add a one-off class.
