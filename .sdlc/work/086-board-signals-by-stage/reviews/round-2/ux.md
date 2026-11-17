VERDICT: PASS

The kept change is in place. `board.html` now shows the approver's word live only at `test` (line 254), reads `was ESCALATE` at `shipped` or `dropped` (line 255), and shows nothing at any other stage. A Ready to close card therefore no longer says it is waiting on the person. The flag at line 250 is gated to `test` as well, and the `pending` flag at line 249 to `build`, matching `column()` and `next_action()` in `board.py`.

- DECISION: [default] Whether a shipped escalated card should keep `was ESCALATE` at all, or drop it and rely on Ready to close alone. Recommendation: keep it. The intent's open question asks for the history to stay visible, and the `was` prefix makes it read as past. If you'd rather a closed card say nothing about the decision, delete line 255 and the `shipped`/`dropped` branch falls to `null`.

## Notes

- **Read:** both screenshots (`round-2/index-1280x800.png`, `index-390x844.png`), `intent.md` (Tier 1, so no `spec.md`; I used the intent's Outcome and Approach), `scripts/board.html` in full, `column()` and `next_action()` in `scripts/board.py` (lines 572–610), and the board paragraph of `docs/REFERENCE.md` (lines 450–459).
- **Not seen:** the screenshots show no shipped, dropped or escalated card, and no stopped or pending card at `build`. I judged those states from the code (`board.html` lines 249–255, `board.py` lines 582–610), and they read consistently with the Outcome. The `test_board.py` changes were not read, since this review is about what the person sees.
- **Smaller findings:**
  - `scripts/board.html:191-198`: the round chip `kept 1 · dropped 2` is explained only in its `title` tooltip ("the verifier kept / dropped"). Keyboard, touch and screen-reader users never get that explanation. Put the words in the chip's text, or in a visible line, for example `verifier kept 1, dropped 2`.
  - PREEXISTING: `scripts/board.html:44`: below 760px the seven columns stack in stage order, so Needs you, the one column that waits on the person, sits after every other column. The 390px screenshot shows only Plan, Design and the start of Build. This may predate this change; if so it is for later. A possible fix is to put Needs you first at narrow widths.
  - PREEXISTING: `scripts/board.html:113-124` and the `aria-modal` drawer: Escape closes it and focus returns to the card, but Tab can move into the page behind the scrim. No focus trap is in the script.
  - The `T1`, `T2`, `R1 … R2 of 2` and `kept/dropped` tokens are jargon to a person who hasn't read the process docs. They are the board's existing vocabulary, so I'm not raising them as a change.
- **What it does well:** the reworked chip separates the live word from history by text (`ESCALATE` against `was ESCALATE`), not by colour. The card, its flag and its `next:` line now agree at every stage, and every node is still built with `textContent`.
