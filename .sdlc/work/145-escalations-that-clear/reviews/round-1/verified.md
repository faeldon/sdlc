The change is kept. R10 names one test, and plan.md line 96 gives it the name `test_nothing_rewrites_decision_md`, but no test has that name. The only match for that name in the repo is plan.md line 96. The spec's R10 asks for a single test that runs `ask`, `decisions`, `sdlc.py gate`, `land-check` and the board's state on an escalated change and finds `decision.md`'s bytes unchanged.

The byte checks that do exist are partial:
- tests/test_factory.py:842-855 checks `decisions` alone.
- tests/test_factory.py:4149-4172 checks restart only.
- `land-check` has no byte check on `decision.md`.

- KEPT: test: C1: tests/test_factory.py: no `test_nothing_rewrites_decision_md`; R10's single test running `ask`, `decisions`, `sdlc.py gate`, `land-check` and the board's state, then comparing `decision.md`'s bytes, doesn't exist

## Notes
I only grepped the tests and read tests/test_factory.py lines 835-860. I ran no tests. I didn't open tests/test_board.py or tests/test_hand_gate.py beyond a grep for `decision.md`, which found line 710 in test_hand_gate.py. A test elsewhere that covers all five commands would settle it, but a grep for the plan's name found none.
