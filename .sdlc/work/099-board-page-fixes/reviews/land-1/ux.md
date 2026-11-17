VERDICT: PASS

I found no CHANGE. The phone order, the drawer's Tab trap and the verifier chip's visible text all match the intent's Outcome, and the builder's round-2 rework (DOM order, not CSS `order`) answers the reach problem from round 1.

- PREEXISTING: scripts/board.html:204-209: the review chips (`ux 1`, `build`) say whose count or step they are only in a `title` tooltip, the same gap as 2026-11-17-26 but on the review chips, which this change does not touch; file it for later.

## Notes

**Read:** both landing screenshots (1280×800 and 390×844), `intent.md` (Tier 1, so its Approach is the spec; there is no `spec.md`), `decisions.md` (D1–D4; D2 is superseded by D3/D4, and D1 and D3/D4 are settled), `build/land-1.md`, all of `scripts/board.html`, and `tests/test_board.py` around the new tests (lines 855–947). I had no shell, so I could not run `git diff main`; I reviewed the page as it now stands on the branch, which is the whole change. I did not open the page in a browser, so the drawer, the phone layout and focus behaviour are judged from the code and the screenshots.

**Screenshots:** at 1280 the seven columns keep stage order and Needs you stays last, as the spec asks for desktop. At 390 Needs you leads, with the 099 card's `was ESCALATE` and the red flag visible, and the other columns follow with their `—` empty markers. The verifier chip reads `verifier: kept 1 · dropped 0` in the visible text on both widths.

**Unseen states, judged from code:**
- Loading shows "connecting…" in the header, then the live time. Fine.
- Board unreachable says "the board isn't answering: is `sdlc.py board` still running?", which says what to do next.
- Empty column shows "—" with no sentence. It is terse, but the spec does not ask for more, so I did not raise it.
- Drawer with no files says "This folder holds no file yet."
- Drawer file read failure says "`<path>` can't be read (`<status>`)." It is terse, but the drawer code is not changed by this review's round.

**Judged from code, working:**
- Tab and Shift-Tab wrap inside the drawer, and focus outside it is pulled back in.
- Escape closes the drawer.
- Focus opens on the drawer's close button and returns to the card that opened it.
- Keyboard users reach the cards via native buttons, so Enter and Space open the drawer.

**Smaller points, not raised as CHANGE:**
- `closeDrawer` returns focus to the card by `data-change`. If that card has gone from the board, focus falls to the page top; say so in `notes.md` or leave as is.
- On a phone the whole board is rebuilt on each width change and each poll that alters the state, and `main` is `aria-live`. That re-announces the board to a screen reader, which is the poll problem the intent defers to 2026-11-17-50. It is not this change's to fix.
- The chip uses the factory's word "verifier", which a person may not know. The title tooltip says it, and D1 chose visible text on purpose, so I left the wording alone.
- The card's focus ring is a border colour change only (`.card:focus-visible`, board.html:62). It is visible, but thin; this change does not alter it.
