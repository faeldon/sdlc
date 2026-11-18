VERDICT: PASS

## Notes

Screenshots read: `index-1280x800.png` and `index-390x844.png`.

- At 1280px the board reads cleanly. Card 012 shows the landing track as its own row (`landing L1`, then ✓ ship, ✓ rebase, ✓ gate, `now: review`, verify, close). It uses the same `.track` chips as the build row above it. The "base moved 1 of 3 times" line sits below the track in the muted style.
- At 390px the board stacks into one column and nothing overflows or clips sideways. The track chips wrap within the card (card 008's B2 row wraps onto a second line). Card 012 (landing track) is in the Ready to close column, which the phone screenshot doesn't reach, so I couldn't check the landing row at that width. It reuses `.track` with `flex-wrap: wrap`, so I expect it to wrap the same way.
- The "landing stopped: …" flag (`board.html:456`) uses the existing `.flag` class, so it matches the other red flags. No screenshot shows it, because no card in the fixture is in that state.
- The "was ESCALATE" and "was READY" badges (cards 010 and 012) look like the other badges.
- What the change does well: it reuses existing styles. The landing row uses `.track` and `.r` instead of adding new classes, and the colours match the build row's done, now and pending chips. A card in the landing keeps the same hierarchy as a card in the build.
