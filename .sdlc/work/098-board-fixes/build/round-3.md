Round 3 is built and the gate is green (2051 passed, 9 skipped). Nothing is committed.

**What round 3 does**
- **The reorder.** In `next_action()` (`scripts/board.py`), the rebasing check now comes before the missing-stage check. A change whose `intent.md` is conflicted mid-rebase now says how to resolve or abort the rebase, instead of "fix intent.md's frontmatter". This was the open ux finding from round 2.
- **The full order, stated once.** `next_action()`'s docstring now lists every state a card can be in, highest first: rebasing, missing stage, problems, closed, stopped, decision pending, approver decided, factory building, red gate, then the stage's own step. A card in two states names the higher one's step.
- **The test.** `test_a_card_in_two_states_names_the_higher_ones_step` pairs every state with every lower one and checks the full text of the step named. That pins "fix what its problems name" too, which the ux reviewer said nothing pinned. Pairs that would need two different stages can't happen and are skipped (9).
  - The first run had 5 failures. Four came from a bug in the test's own helper (it used `None` to mean "no stage yet", and `None` is also a real stage); I fixed it. The fifth was the rebasing vs. missing stage pair, the open finding, which went green after the reorder. No other pair was in the wrong order.

**What changed in `plan.md`**
- A new section, *The precedence of `next_action()`*, holds the full table and says why it's in that order.
- The bullet that only named the pairs reviews had raised now points to that table.
- The Tests section lists the new test, and the work order records round 3.

**`notes.md`**
- The ux line is ticked as done.
- I added two unticked lines from the round-2 code notes for you to dispose of at ship:
  - A card with a problem and a pending decision at `build` names only the problem. That follows the table's order on purpose, but the card no longer says a decision is waiting.
  - The `--abort` wording doesn't say the resolved work is kept under `refs/sdlc/end/<branch>`.
- The five earlier lines about the page's layout are still unticked, as before.

No decisions raised this round. D1 and D2 are already answered in `decisions.md`.

## Evidence

$ uv run --group dev pytest -q tests/test_board.py -k higher_ones   (before the reorder, after fixing the helper)
FAILED tests/test_board.py::test_a_card_in_two_states_names_the_higher_ones_step[rebasing-stage missing]
1 failed, 45 passed, 9 skipped, 55 deselected in 1.57s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py
101 passed, 9 skipped in 27.18s
exit: 0

$ ./check.sh
2051 passed, 9 skipped in 40.34s
✔ Validation passed
exit: 0
