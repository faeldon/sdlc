VERDICT: CHANGES

- CHANGE: scripts/board.html:324: `render()` reads `open` on line 324 (`held && !open`). Line 330 declares `const open` in the same function, so line 324 hits that local binding before it is initialised. That throws a ReferenceError whenever a card has focus, which is the case this change exists to protect. When it throws, the focus restore, the totals line and the status update are all skipped. `poll`'s catch then shows "the board isn't answering" even though the server is fine. Rename the local count (for example `openCount`) so the drawer's `open` is the one used.

## Notes

Read: both screenshots (1280 and 390 widths), `intent.md`, and `board.html` (card, render, poll and the drawer open/close code). I did not read `spec.md`, `decisions.md`, `board.py`, `sdlc.py` or the `status` skill, so I did not check the "What needs me" line in `/sdlc:status`. I could not see the drawer, the "board isn't answering" state or the focus behaviour. I judged them from the code. The `needs` text is built with `textContent`.

Smaller findings:
- The screenshots show 100's card with "needs you: read the escalation" and, just above it, the flag "the approver escalated it to you". Both say the same thing.
- Ready-to-ship cards 104 and 106 carry both an "escalated: answered" badge and an "ESCALATE" chip. The chip reads like an open escalation. Consider hiding it when `answered` is true.
- In the "Needs you" column header, "what each card says it needs" is a sentence where the other columns use short labels. That is fine, but it is long at narrow widths.
- On the phone layout, "Needs you" is the first column. That is the right priority.

Done well:
- Each card in Needs you states what the person has to do, in red and in plain words. The status line gives a count, "live · 1 needs you".
- `aria-live` now sits on the status line alone.
- The render key is built from what the screen shows (`shownAs`), so a poll that changes nothing visible rebuilds nothing.
