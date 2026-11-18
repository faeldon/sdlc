VERDICT: PASS

I judged the card states from the two screenshots and the `board.html` hits for labels and ARIA. I did not read the full diff.

## Notes
- **Read:** `intent.md`, the 1280×800 and 390×844 screenshots, and `scripts/board.html` (grep for labels and ARIA only).
- **Task and wording:**
  - A stopped card sits in Needs you with a plain line, a bold `needs you:` line and a `next:` command. For example, card 006 reads `stopped: rerun to ask an agent again` and `rerun /sdlc-factory:build 006, or /sdlc:ship 006`.
  - Card 007's decision line names where to go (`decide D1 in the session running …`).
  - Round labels read `B1`, `B2` and `landing L1`, matching the intent.
- **Reach:** the board's controls are real buttons with labels. The drawer is `aria-modal`, with a Tab cycle, a labelled close button and a labelled Files nav. At 390px the columns stack, and Needs you comes first, which suits that width.
- **Not seen:** I saw no screenshot of a stopped landing on a shipped card (the `/sdlc:close NNN` way on) and none of a `stuck` or `untestable` stop. I took those from the intent only, and they are the weakest part of this review.
- **Smaller findings, none blocking:**
  - Card 007's `next:` text wraps long at 1280px, and the card is clipped at the bottom of the screenshot. This is a layout nicety, not a block.
  - Card 007 repeats the decision in both the red line and `needs you: decide D1`. That is acceptable.
- **Done well:** every stop pairs a plain reason with a concrete next command, and the stopped landing keeps its card on the track at its step (`now: review`, `base moved 1 of 3 times`).
