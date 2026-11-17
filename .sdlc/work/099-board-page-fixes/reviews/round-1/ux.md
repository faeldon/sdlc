VERDICT: CHANGES

- CHANGE: scripts/board.html:47: at phone width `.col.needs-you { order: -1 }` puts Needs you first on screen, but `render()` (lines 287-294) still builds the columns in DOM order, so Tab reaches Needs you last, after every card in Plan through Ready to close. The spec asks for a focus order that follows the page, and a keyboard or switch user on a phone gets the reverse of what a sighted user sees. Fix: at or below 760px, have `render()` put the `needs-you` section first in the DOM (for example with a `matchMedia("(max-width: 760px)")` check and a re-render on change), and keep the desktop DOM order. The test at tests/test_board.py:891 pins the CSS-only approach and will need to change with it. This is the point the builder deferred as D2 in decisions.md; I'm raising it as a CHANGE because the reach requirement is not a trade-off between two users.

## Notes

- **Read:** both screenshots (1280x800 and 390x844), `intent.md`, `decisions.md`, `scripts/board.html` in full, and `tests/test_board.py` at the new tests (lines 888-932). The change folder has no `spec.md` (Tier 1), so the intent's Outcome and Approach stand in for it. I could not see the diff itself, only the current file.
- **Shown in the screenshots:** the 390px view has Needs you first, which meets the phone-order outcome. Desktop keeps stage order. The Needs you column is empty in both shots, so the order is verified but its content is not.
- **Not seen, judged from code:**
  - *Loading:* the header reads "connecting…" until the first poll. Acceptable.
  - *Error:* "the board isn't answering: is `sdlc.py board` still running?" (line 310) says what happened and what to do. Good.
  - *Empty column:* a bare "—" (line 292). The change puts an empty Needs you at the top on a phone, so a phone user first sees a dash under "NEEDS YOU". It misleads no one, so it is not a CHANGE, but a plain "Nothing needs you" would read better.
  - *Drawer with no files:* "This folder holds no file yet." (line 339). Clear.
  - *Verifier chip:* no screenshot has a verified round. From the code, "verifier: kept N · dropped M" is visible text, which meets the outcome (D1 is the right call).
- **Drawer:** the Tab trap, Escape, and focus return (lines 350-374) work as the spec asks. Focus return looks the card up when the drawer closes, so it still works after the 2-second re-render. If the change has closed in the meantime, focus falls to the page body. Minor.
- **Pre-existing, not this change's:** `aria-live="polite"` sits on the whole `#board` (line 139), so every state change can make a screen reader read the whole board again. If that was already so before this change, it is for a later round.
- **Done well:** the trap's wrap-around and its pull-back for focus that has left the drawer, the `.doc` pane made a Tab stop with a name, and the chip text naming the verifier, which fixes the tooltip-only problem for every user.
