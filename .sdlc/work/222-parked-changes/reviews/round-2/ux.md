VERDICT: PASS

The kept security change is fixed and tested. The board screenshots show no UX problems.

## Notes
- **Kept change, checked:** `factory.py:4008-4012` now works out `changed` before the busy branch. A busy answer parks only when `not changed`. If the tree changed, the attempt is written as a FAIL with `Tree: changed: …`. `tests/test_factory_park.py:150-161` covers it: the check edits `README.md` and exits 75, a FAIL attempt is written, and `runs/parked.md` is not. This matches the kept change's fix.
- **What I read:**
  - The 1280 and 390 screenshots of the board.
  - `scripts/board.html` (the `parked` step style and the `⏸ ` step word).
  - `factory.py` around the gate and its busy handling.
  - The park test file.
- **What the screenshots don't show:** The fixture has no parked card, so I couldn't see how one looks. I judged it from `board.html`. A parked step gets a dashed border and a `⏸ ` prefix, so it is told apart by more than colour and still reads on a phone-width layout.
- **Phone width:** The cards stack in one column, and the "needs you" text and the `next:` command stay readable.
- **Done well:** A busy check that changed the tree is a visible FAIL and names the changed paths. It no longer parks silently with an edit hidden from later reviewers.
