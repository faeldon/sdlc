VERDICT: PASS

The only UI change is a "gate green" or "gate red" badge in `scripts/board.html`. The badge only appears on a by-hand card with a current gate record. Every card in the screenshots is a factory card, so none shows it. The review therefore rests on the code and on the layout around it.

## Notes
- **Screenshots read:** `index-1280x800.png` and `index-390x844.png`. Neither shows the new badge.
- **Layout:** both widths hold. There is no overflow or clipping, and the columns stack cleanly at 390px with the badges wrapping.
- **Styling:** the badge reuses the existing `.badge` class and the `--accent` and `--stop` tokens (`board.html:71-72`). There are no hard-coded colours.
- **Contrast:** the badge's meaning is in its text ("gate green" or "gate red"), not colour alone. The colour tokens themselves were not checked for contrast.
- **Not checked:** the badge was never seen in a render. At 390px, a by-hand card with the mode badge, the gate badge and an existing status badge may wrap. That is a small risk.
- **Done well:** the change reuses the existing badge styling and tokens, and the label carries the verdict in words.
