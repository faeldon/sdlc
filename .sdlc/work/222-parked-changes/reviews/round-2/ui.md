VERDICT: PASS

The kept security change is fixed. In `plugins/factory/scripts/factory.py:4008-4012`, `cmd_gate` now works out `changed` first. It treats a busy answer as busy only when `not changed`. A busy run that edited the tree falls through to a normal attempt: `FAIL`, with `Tree: changed: …`, and no park. `tests/test_factory_park.py:150` covers this. It asserts `exit == "75"`, `tree == "changed: README.md"`, a `GATE: FAIL` record, and no `runs/parked.md`. I only read the code and test, and ran nothing.

This change has little UI. The only styling change I found is `scripts/board.html`:
- `.step.parked { border-style: dashed; }` at line 104.
- The `⏸ ` word for a parked step at line 436.

Neither screenshot shows a parked step, so those two lines are checked by reading alone.

## Notes
- **Screenshots read:** `index-1280x800.png` and `index-390x844.png`.
  - At 1280px the six columns align and the card text wraps without overflow.
  - At 390px the board stacks into one column with no sideways scroll, and the step chips wrap cleanly.
- **Parked step not shown:** the fixture has no parked card, so the dashed border and the `⏸` marker are unconfirmed. They reuse the existing `.step` class and neighbouring pill styling, so I don't expect a problem.
- **Done well:** the new `parked` state is one modifier on the existing `.step` chip, not a new component. It also doesn't rely on colour alone, since the dashed border and the `⏸` glyph both mark it.
