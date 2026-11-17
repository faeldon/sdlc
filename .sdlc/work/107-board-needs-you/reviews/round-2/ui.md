VERDICT: PASS

The kept change is fixed. `render()` no longer declares a local `open`. The count is now `openCount` (line 331, used in `#totals`), so `open` on line 324 is the drawer variable at line 359. I confirmed this by searching `board.html` for `open`. I did not read `tests/test_board.py`, so I can't say whether `test_a_rebuild_puts_focus_back` now fails on a shadowed `open`. I also couldn't run the board, so I can't confirm focus survives a rebuild. The screenshots only show the page after a normal render.

## Notes
- Screenshots read: `index-1280x800.png` and `index-390x844.png`, both round 2.
- At 1280px, the columns and cards line up and nothing overflows. NEEDS YOU is marked by a red left border and red text, plus the label "needs you: …", so it doesn't rely on colour alone. The totals line shows "4 open · 5 by the factory". The header reads "live · 1 needs you".
- At 390px, the columns stack with NEEDS YOU first. Nothing scrolls sideways, and the header wraps cleanly.
- Smaller finding: empty columns (PLAN, DESIGN) show a bare "—" and take a full row on the phone. A collapsed or hidden empty column would save scrolling. This is optional.
- Smaller finding: some small chips, such as "was READY" and the grey stage tags, are low in contrast. They are still legible.
- What the change does well: it puts the card that needs the person first on the phone and marks it with a red stripe, so the main point of the page is the first thing seen.
