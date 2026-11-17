VERDICT: PASS

The change does what the intent asks, as far as I can see from the screenshots and the code. The one gap is that the empty-column and unreadable-stop states aren't in the screenshots, so I judged them from the code, not from a render.

## Notes

**Read:** both screenshots (`index-1280x800.png`, `index-390x844.png`), `intent.md` (Tier 1, so the Approach stands in for `spec.md`, which doesn't exist), `scripts/board.html` in full, `scripts/board.py` (`_stopped`, `next_action`, `column`), `needs_of()` in `scripts/sdlc.py`, and the REFERENCE.md board section. `decisions.md` doesn't exist, so nothing is settled or open there. I didn't run the server or a browser.

**Checked against the screenshots:**
- At 1280px every column (Plan, Design, Build, Test, Ready to ship, Ready to close, Needs you) shows its subtitle on its own line under the heading, left-aligned with it. That covers the 052 fix.
- At 390px Needs you leads, with its heading, count and subtitle stacked as intended. The 006, 007 and 008 cards show a `needs you:` line and a `next:` line that agree.

**States judged from code, not seen:**
- Empty column: `board.html:323` shows "nothing waiting here" in place of the bare "—". This meets the intent's wording.
- Unreadable `runs/stopped.md`: `_stopped()` gives `way: None`, `next: read runs/stopped.md`, and `needs_of()` gives `stopped: read runs/stopped.md`. The card and `status` now agree.
- Loading: the status line says "connecting…" and the board is empty until the first poll. That was already so and isn't this change's.
- Error: "the board isn't answering: is `sdlc.py board` still running?" says what happened and what to check. Good.

**Smaller findings:**
- The unreadable-stop flag reads `stopped: runs/stopped.md doesn't open with STOPPED: and its NEXT: line`. "STOPPED:" and "NEXT:" are file keywords a person may not know. Consider naming what's missing in plain words, for example "its stop record has no STOPPED or NEXT line".
- "nothing waiting here" in Plan, Design or Build can read as "nothing to do" rather than "no change is at this stage". It meets the intent, so this is a wording choice, not a fault.
- In the 1280 Needs-you column, the build-stage decision text "decide D1 in the factory's supervisor" names a place the page never says how to reach. This wording predates the change, so I'm not raising it as a change.

**What it does well:** the subtitle fix is CSS only, with the subtitle in its own grid row, so it holds at every width. The phone layout puts the column that waits on the person first, in DOM order as well, so Tab reaches it first. And `next_action()` now follows the same `needs` list as the card's `needs you:` line, so the two can't drift apart.

- PREEXISTING: `scripts/board.html:292`: a stop's `next:` is a long run-on command in monospace (006's "rerun /sdlc-factory:build 006, whose one mend asks again…"), and it wraps badly at 390px. The text comes from the factory's stop record, which this change doesn't touch.
