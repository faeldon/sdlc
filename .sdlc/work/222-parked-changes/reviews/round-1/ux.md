VERDICT: PASS

I couldn't see a parked card in either screenshot, so I judged parked from the code. The gate record was not in my reading list, so I didn't read it.

## Notes

- **Read:** both screenshots (1280×800 and 390×844), `intent.md`, and the parked parts of `scripts/board.py`, `scripts/board.html` and `scripts/sdlc.py`. I did not read the factory's `verdicts` code, `build/SKILL.md`, the docs or the tests.
- **Screenshots:** the fixture has no parked card. The cards shown are the existing ones, and they render fine at both widths. At 390px the board is a single column with `NEEDS YOU` first, which is the right order for a phone.
- **Parked state, from the code:**
  - The gate step on the track reads `⏸ parked on <resource>, held by <holder>; retry <t>, deadline <t>`.
  - `status` shows the same line, split in two at the `; `.
  - Past the deadline, the card gets the need `parked past its deadline: free <resource>`, which puts it in `NEEDS YOU`.
  - A stopped park says `free what it waits on and rerun`.
  - Each state says what happened, and the state is carried by the `⏸` glyph and the words, not by colour alone.
- **Minor, board card:** while a park is within its deadline, the card's `next:` line falls through to the generic "the factory is building it: wait for its decision". That is accurate but doesn't say the change is waiting on a host resource. Consider a `next` like "waiting on <resource>; the factory retries at <retry>" (`scripts/board.py` ~line 723).
- **Minor, board styling:** `.step.parked { border-style: dashed; }` (`scripts/board.html:104`) sets no border colour, and `.step` has a transparent border. The dashed outline is invisible, so a parked step looks like a plain chip. The text still distinguishes it. Give it `border-color: var(--muted)`.
- **Minor, width:** the parked label is long: resource, holder and two timestamps in a single `.step` chip. At 390px it wraps inside the chip but stays readable, because `.track` has `flex-wrap`.
- **Done well:** the park line is one shared function (`park_line`), so the board and `status` use the same words. A park past its deadline becomes a visible need instead of waiting forever. The `⏸` glyph is paired with text.
