VERDICT: PASS

The kept change from round 1 (C1, the missing R10 test) was made. `test_nothing_rewrites_decision_md` is now in `tests/test_land.py`. It builds an escalated change with a `gate` and a `look` reason, then runs `decisions`, `ask`, `sdlc.py gate`, `land-check` and the board's state in turn. After each step it asserts `decision.md` is byte-identical, and the assertion message names the step. `plan.md` line 96 now points to the new location.

## Notes
- The test ends by checking that the board card shows `ESCALATE` and needs "acknowledge D1". That confirms the escalation was actually read, not just left untouched.
- The round-2 gate record `build/round-2.gate.md` is green (`./check.sh`, exit 0). I ran neither the gate nor any test.
- I reviewed only what the rework touched (that test and the `plan.md` line). Round 1's code review passed the rest, and nothing new is raised there.
- Done well: the builder confirmed the test can fail by making `ask` append to the file, saw the failure name `ask`, and then restored `factory.py`.
