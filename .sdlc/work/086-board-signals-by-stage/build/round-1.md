The board now checks each factory signal only at the stage it belongs to. A shipped or dropped change goes to **Ready to close** whatever its `decision.md` or `decisions.md` still say, and a file that won't read stays under **Needs you** at any stage. The gate passes with 1905 tests, and the work is left uncommitted.

**What changed**
- **`scripts/board.py`, `column()`:** a file that won't read still comes first. Then shipped or dropped means Ready to close, then a stopped run or a blocking decision counts only at `build`, then ESCALATE or READY only at `test`, then how far the change has got.
- **`scripts/board.py`, `next_action()`:** a pending decision is named only at `build`. The order already put shipped and dropped ahead, and the stop record was already read only at `build`.
- **`scripts/board.html`:** the card's "waits on you" and "the approver escalated it to you" flags follow the same rule, so a card in Ready to close doesn't still say it waits on the person. The ESCALATE badge stays, which answers the intent's first open question with "the badge is enough".
- **`docs/REFERENCE.md`:** the account of **Needs you** now says each signal counts only at its stage, and that the stage is how the board knows the person answered.

**Tests added (`tests/test_board.py`)**
- `test_each_factory_signal_counts_only_at_its_stage` covers the six ways out the intent lists:
  - escalated then shipped → Ready to close, `/sdlc:close 020`
  - escalated then dropped → Ready to close
  - escalated, fixed by hand, still at `test` → Needs you
  - escalated then put back to `build` by hand → Build, the old ESCALATE ignored
  - stopped then shipped by hand → Ready to close
  - a pending blocking decision at `shipped` → Ready to close

  It failed first because four of those cards were still under Needs you.
- `test_a_file_that_wont_read_needs_the_person_at_any_stage`: a shipped change whose `decision.md` won't read stays under Needs you. It passed before the fix too; it is there to keep that rule in place.

The tests that already covered the existing cards (running, READY at `test`, stopped at `build`, deciding at `build`, built by hand) pass unchanged.

The page has no test runner, so `checks.md` holds one acceptance check: a `grep` that the two stage-gated flag lines are present. It exits 0.

**Two things not done**
- A factory change put back to `build` with an old `decision.md` still shows its step track as all done. That's because `test_a_decision_or_a_stop_overrides_the_record` deliberately treats a decision at `build` as done: the supervisor writes `decision.md` just before moving the stage to `test`. The files can't tell that moment from a stage moved back by hand. I tried gating it, it broke that test, and I reverted it. The column is right; only the step track is stale.
- `/sdlc:status` needs no change: `sdlc.py` reads `decision.md` only for measuring, not for status.

There is no `plan.md`: this is Tier 1, and the Approach named only `board.py` and the tests. Nothing was added to `notes.md`.

- DECISION: [default] Should the card's flags in `board.html` also count each signal only at its stage, beyond the `column()` and `next_action()` the intent names? Options: gate them; leave them. Going ahead with gating them: otherwise a Ready to close card still says it waits on the person.

## Evidence

$ ./check.sh > /tmp/086-gate.log 2>&1; grep -E "passed|failed" /tmp/086-gate.log | tail -3
1905 passed in 40.54s
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest tests/test_board.py -q -k "its_stage or any_stage"   (before the fix)
FAILED tests/test_board.py::test_each_factory_signal_counts_only_at_its_stage
1 failed, 1 passed, 40 deselected in 4.95s
exit: 1

$ uv run --group dev pytest tests/test_board.py -q   (with the `_progress` gate, since reverted)
FAILED tests/test_board.py::test_a_decision_or_a_stop_overrides_the_record - ...
1 failed, 41 passed in 15.11s
exit: 1

$ uv run --group dev pytest tests/test_board.py -q
42 passed in 13.46s
exit: 0

$ uv run --group dev pytest tests/test_board.py -q -k "its_stage or any_stage"
2 passed, 40 deselected in 2.66s
exit: 0

$ sh -c "<checks.md's sh block>"
exit: 0
