All three board-page fixes are built and left uncommitted, and the full gate passes. The new tests only read the page's source, so nothing ran the focus trap in a real browser.

This is a Tier 1 change touching two files (`scripts/board.html`, `tests/test_board.py`), so there's no `plan.md`.

**Slices built (all in `scripts/board.html`):**
1. **Phone order (2026-11-17-24):** below 760px, the Needs you column now comes first. The desktop layout is untouched.
2. **Drawer keyboard trap (2026-11-17-25):** while the file drawer is open, Tab and Shift-Tab cycle among the drawer's own buttons and links. If focus is somewhere behind the drawer, the next Tab pulls it back in. Escape still closes the drawer and focus returns to the card that opened it; both already worked and are now pinned by a test. The scrolling file pane is now a Tab stop with a name ("File contents") and a focus outline. Without that, Chrome lets Tab reach the pane and from there leave the drawer.
3. **Verifier chip (2026-11-17-26):** it now reads `verifier: kept N · dropped M`, so keyboard, touch and screen-reader users all get it. The tooltip stays. Every node is still built with `textContent`.

**Tests added (`tests/test_board.py`, all marked portable):**
- `test_needs_you_comes_first_at_phone_width_and_nowhere_else`: Needs you is first in the 760px stacking rule, and no column order is set outside it.
- `test_the_open_drawer_keeps_tab_inside_it`: the trap handler wraps focus both ways and pulls stray focus back. The keydown handler acts only while the drawer is open, sends Escape to close and Tab to the trap, focus returns to the card, and the file pane is a named Tab stop.
- `test_the_verifier_chip_says_whose_count_it_is_in_its_text`: the chip's visible text names the verifier.

I ran all three against the original page and each failed for the expected reason, then passed after the fix.

**Gate:** `./check.sh` passes, 2001 tests.

**Left in `notes.md`:**
- [ ] On a phone, Needs you is now first on screen, but Tab and screen readers still reach it last. Building the columns in phone order in the page's render step would fix that.
- [ ] No browser test exercises the trap; that would need a dependency the gate doesn't have.

**Decisions:**
- DECISION: [default] Label on the chip: visible or accessible-only (the intent's open question)? Options: visible text; `aria-label` or a visually hidden label only. Going ahead with visible text `verifier: kept N · dropped M`. Only visible text reaches sighted keyboard and touch users, who are part of the bug. Browsers also often ignore an `aria-label` on a plain span. The chip only gets wider.
- DECISION: [default] Phone order by CSS `order` alone, as the Approach says, or by also reordering the page so Tab follows what's on screen? Going ahead with CSS alone, with the reordering logged in `notes.md` as a follow-up.

## Evidence

$ uv run --group dev pytest -q tests/test_board.py -k "phone_width or keeps_tab or verifier_chip"   # with HEAD's board.html in place
FAILED tests/test_board.py::test_needs_you_comes_first_at_phone_width_and_nowhere_else
FAILED tests/test_board.py::test_the_open_drawer_keeps_tab_inside_it - Assert...
FAILED tests/test_board.py::test_the_verifier_chip_says_whose_count_it_is_in_its_text
3 failed, 48 deselected in 0.06s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py
51 passed in 18.25s
exit: 0

$ ./check.sh
All checks passed!
205 files already formatted
2001 passed in 71.23s (0:01:11)
✔ Validation passed
exit: 0
