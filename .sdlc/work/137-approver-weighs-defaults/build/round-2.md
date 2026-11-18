I've addressed all three kept changes. Status and the board now point the person to `/sdlc-factory:decide NNN`, and the decide skill says what to do when `ask` refuses. The full gate passes (`./check.sh`: 2457 passed, 17 skipped). Nothing is committed.

## Kept changes
- **ux C1 (`scripts/board.py`).** An escalated card at `test` that still has a decision or defaults to confirm now names the skill as its next step, for example `/sdlc-factory:decide 016 for D2 and 1 default, then /sdlc:ship, or /sdlc-factory:land with the others ready`. A card with only defaults to confirm used to go straight to ship; it now gets the same step. A blocking decision at `build` still says "in the factory's supervisor". The board and status both get this from one new function in `sdlc.py`, `decide_step()`. The board's step-order table gained a "defaults to confirm" case and its pairing with the "escalation pending" case. Two expected texts changed: that table's "escalation pending" row and `test_an_escalation_names_the_decision_it_still_needs_first`.
- **ux C2 (`scripts/sdlc.py`).** In status's `■ What needs me`, the line for such a change now ends with the command, for example `041  decide D3, confirm 2 defaults  /sdlc-factory:decide 041`. I added this where status prints the line, not to the texts in `needs_of()`. Those texts stay the same because the spec's Boundaries rule out new `needs_of` text. `test_status_ends_with_what_needs_me` now expects the command, and REFERENCE.md's needs and board paragraphs say this.
- **ux C3 (`plugins/factory/skills/decide/SKILL.md`).** Step 0 now says, for each refusal, what the person can do instead:
  - At `build` or `design`, answer the blocking decisions in the session running `/sdlc-factory:build`, and come back once the run reports the change ready to ship.
  - At `plan`, the change isn't built yet.
  - At `shipped` or `dropped`, there is nothing left to decide.
  - For a number that names no change, the skill repeats what `ask` said and points to `/sdlc:status`.

  A new test, `test_decide_says_what_to_do_instead_when_ask_refuses`, pins this text.

The board and status tests failed in 11 places before the code went in, for the reason expected. I wrote the C3 test after its text, so I never saw it fail.

**`plan.md`:** I added a paragraph on this round's rework. There's nothing new in `notes.md`.

## Decisions
Round 1's two defaults reached the ledger without their options. I'm raising them again with the same text, to fill those lines in once:

- DECISION: [default] A default the approver settled stops a batch from landing on its own (R9, which `spec-questions.md` left to you). Going ahead with that unless told otherwise.
  - OPTION: a landing signal — you see every approver call before it reaches main; fewer batches pass by themselves
  - OPTION: no signal — a READY batch whose only open items the approver settled lands `by=auto`, which helps O6 more; an agent's call reaches main without you seeing it
  - WHY: the spec as approved has R9, and its Boundaries put it under "Asks first"
- DECISION: [default] Keep the change that stops the landing listing and signalling a superseded default as assumed in this change, not split out. Going ahead unless told otherwise.
  - OPTION: keep it here — `open` is one check across `verdicts`, `decisions` and the landing; it changes the landing's signals slightly
  - OPTION: split it out — this change stays narrower; the landing keeps the old check that counts superseded lines as assumed
  - WHY: R8 asks for this check, and it matches what 105 R7 already says a superseded line is

## Evidence

$ uv run --group dev pytest -q -n auto tests/test_board.py
11 failed, 138 passed, 17 skipped in 17.82s
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_board.py tests/test_sdlc.py
389 passed, 17 skipped in 12.70s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_skills.py
375 passed in 18.56s
exit: 0

$ ./check.sh > /tmp/c137.log 2>&1; echo "exit: $?"; grep -E "passed|failed|All checks|already formatted|Validation" /tmp/c137.log
exit: 0
All checks passed!
259 files already formatted
2457 passed, 17 skipped in 77.71s (0:01:17)
✔ Validation passed
✔ Validation passed
exit: 0
