VERDICT: PASS

The rework does what the kept change asked. The `ESCALATE` chip now appears only at `test`, and a shipped or dropped change shows `was ESCALATE`, which doesn't say it is waiting on the person (`scripts/board.html:252-255`). Neither screenshot shows a shipped or dropped card, so the new label isn't seen at either width. The check rests on the code, not the screenshots.

## Notes

- Screenshots read: `index-1280x800.png` and `index-390x844.png` (round 2).
- The 1280 shot shows 089 in NEEDS YOU with the live `ESCALATE` chip and its test-stage flag, which is the intended behaviour. Ready to close is empty there, so the fix is not visible in that shot.
- The 390 shot stops partway down the page, after BUILD. The NEEDS YOU and Ready to close columns, which this change affects, are not in it, so their layout at phone width is unchecked. Capturing a full-length 390 shot would cover that.
- At 390px the cards wrap cleanly: the round rows and the progress bar stay inside the card, with no overflow or sideways scroll.
- The chip sits on the card's top row beside the number and the mode badge, and wraps onto its own line at 1280. Both readings are legible.
- The `was ESCALATE` label is untested at either width, since no shipped or dropped card is in view. Worth one look on the next capture.
- Good: the stage gate is written once and shared with the flag at line 250, so the chip and the flag can't disagree about which stage counts as live.
