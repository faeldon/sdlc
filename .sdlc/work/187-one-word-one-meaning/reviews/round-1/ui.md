VERDICT: PASS

The change is mostly a rename of terms across docs, scripts and agents. The board page is the only visible surface, and it holds up at both widths. The screenshots never show the new `acceptance: N, passed/failed` text on a card, so I couldn't check it visually.

## Notes
- **Screenshots read:** `index-1280x800.png` and `index-390x844.png`. `decisions.md` is read; D1–D5 are open defaults and none is a UI matter.
- **Desktop (1280):** the six columns line up, the headers and counts are consistent, and the stage pills and badges keep the existing styling. The red needs-you cards still stand out most. Nothing overflows.
- **Phone (390):** the board collapses to a single column with no sideways scroll. The long `next:` lines in monospace wrap cleanly, and the pill rows wrap without clipping.
- **Colour:** state is also given in words (`gate red`, `needs you:`, `ESCALATE`), so it does not depend on colour alone.
- **Not verified:** I didn't diff `scripts/board.html` for hard-coded colours. Nothing in the screenshots looks off-token.
- **Done well:** the renamed column and pill labels (`READY`, `LANDING`, `NEEDS YOU`) keep their length and layout, so the rename caused no wrapping or alignment regressions.
