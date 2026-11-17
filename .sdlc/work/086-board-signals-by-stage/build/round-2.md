I fixed the one kept change: the decision badge on a card now shows only at the stage it belongs to. The gate passes with 1905 tests.

- **KEPT ux C3** (`scripts/board.html`, the badge at line 256): the badge now depends on the change's stage.
  - **At `test`:** it shows the approver's word as before (`READY` or `ESCALATE`), where the decision is still waiting.
  - **Shipped or dropped:** it reads `was ESCALATE` or `was READY`, so a card in Ready to close keeps the history without saying it still waits on the person.
  - **At `build`:** it shows nothing, matching the column, which ignores an old decision there.

  The page has no test runner, so I added a second acceptance check to `checks.md`. It confirms the badge is tied to the stage and the old ungated line is gone. Both checks exit 0.

The two DROPPED lines (C1, C2) needed no action. No test changed, no `plan.md` was written (Tier 1), and nothing was added to `notes.md`.

- DECISION: [default] Show nothing for a decision on a card at `build`? A change only sits at `build` with a decision for a moment before the supervisor moves it to `test`, or after the person moves it back. Going ahead with no badge there, which matches the column ignoring it.

## Evidence

$ sh -c "<checks.md's first sh block>"
check 1 exit: 0
exit: 0

$ sh -c "<checks.md's second sh block>"
check 2 exit: 0
exit: 0

$ ./check.sh > /tmp/086-gate.log 2>&1; grep -E "passed|failed" /tmp/086-gate.log | tail -3
1905 passed in 113.80s (0:01:53)
✔ Validation passed
✔ Validation passed
exit: 0
