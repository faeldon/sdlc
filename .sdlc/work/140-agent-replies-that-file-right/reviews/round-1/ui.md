VERDICT: PASS

The screenshots show the board at both widths, and the 006 "Purge drafts" card shows the new stopped-reply text. I found no layout, overflow or contrast problems.

## Notes
- **Screenshots read:** `index-1280x800.png` and `index-390x844.png`.
- **Desktop (1280):** The columns line up and the card hierarchy reads clearly. The red "stopped: build/round-1.md has no ## Evidence section" line and the bold "needs you" line sit well in the NEEDS YOU column, and the long text wraps inside the card.
- **Phone (390):** The page is a single column with no sideways scrolling. The stopped text, the "needs you" line and the monospace `next:` line all wrap inside the cards. The R1/R2 chip rows wrap too.
- **Not checked:** I didn't read the changes to `scripts/board.py` against the board's CSS. The screenshots show the board uses its existing tokens: red for urgent, blue for factory badges, and the existing chip and card styles.
- **Not shown:** Most of this change is agent prompts and factory logic, which has no visual surface. The one visible piece is the stopped card (the 006 fixture).
- **Does well:** The stopped state reuses the existing red "needs you" treatment, so it looks like the other cards that need the person. It also names the file and the missing section, and the `next:` line says exactly what to rerun.
