VERDICT: PASS

The change doesn't alter how the board looks. The board page is the only screenshotted page, and the changes to `scripts/board.py` appear to be logic and wording. Neither screenshot shows the promotion flow itself, so I judged only the existing board.

## Notes
- I read `index-1280x800.png` and `index-390x844.png`. At 1280px the six columns line up and nothing clips. At 390px the cards stack into a single column that fits the screen, with no sideways overflow. Long `next:` text wraps.
- `board.py` mentions `PAUSES = ("decide", "upgrade", "spec")`. No screenshot shows an upgrade pause card, so I couldn't check how it looks.
- At 390px the header's meta line wraps over three rows, which is a little loose. It's the same as before this change, so I'm not raising it.
- The cards keep a consistent style. Chips, the red "needs you" border, the blue "ready" highlight and the monospace `next:` lines are used the same way across columns, and none of it is hard-coded in this change.
