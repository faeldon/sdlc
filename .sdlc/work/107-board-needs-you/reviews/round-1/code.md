VERDICT: CHANGES

- CHANGE: scripts/board.html:324: `render()` reads `open` in `if (held && !open)`, but the same function declares `const open = st.changes.filter(...)` at line 330. That local shadows the module-level drawer variable `open` (line 359). Reading it before line 330 hits the temporal dead zone, so it throws `ReferenceError` whenever `held` is set. That is exactly the focus case R14 exists for. The throw happens after `replaceChildren` and before the totals update. `poll()`'s `catch` then shows "the board isn't answering" and skips `say()` and `#polled`. So a Tabbed-onto card breaks the board on the next rebuild, and focus is still lost. Fix: rename the local at line 330 (for example `openCount`, and use it in `#totals`) so `open` refers to the drawer. Make `test_a_rebuild_puts_focus_back` fail on this. It only matches the source text, so it can't see the shadowing. Either assert that `render` declares no `open`, or run the script under a DOM stub or node with a focused card.

## Notes

- Optional: R14 says "unless the drawer is open", and `open` is the right variable once the shadowing is fixed. While a drawer is open, `closeDrawer()` restores focus anyway, so that is consistent.
- Optional: `factory_reading()` and `board._factory()` duplicate the ledger scan. The spec accepts this as a pinned-copy pattern. `GARBLED_LEDGER` is shared through `sdlc.`, which is good. Check that `OPEN_BOX` in `board.py` and the literal `"- [ ]"` in `sdlc.py` are covered by the pin test.
- Done well:
  - `needs_of` and `answered` are pure, with one reader for the board and `status`.
  - `column()` is simplified to follow `needs`.
  - Garbled open lines become a problem, not an answer.
  - `status` records only gain keys.
  - The docs and `skills/status/SKILL.md` are updated.
- Ran `pytest -n auto tests/test_board.py tests/test_sdlc.py tests/test_metrics.py`: 436 passed, 9 skipped. I did not run `./check.sh`. I found the shadowing bug by reading `board.html`.
