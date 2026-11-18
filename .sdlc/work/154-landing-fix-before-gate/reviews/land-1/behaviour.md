VERDICT: PASS

The new end-to-end tests pass and the fix is now applied before the first gate. The spec and decision.md were not read, and `checks.md` does not exist. The behaviour review therefore rests on `intent.md`'s Outcome and Approach.

## Notes
- **checks.md:** none for this change, so there is nothing to read or run.
- **Gate record:** `build/land-1.gate.md` shows `GATE: PASS` for `./check.sh`. I did not rerun the gate.
- **Fix before the gate:** in `_train_reading` the `fix` step now comes right after a change is stacked, or committed when it didn't move. It sits before step 3, the tip gate. `test_a_fix_the_gate_needs_is_made_before_the_gate` stacks two changes and checks that the reading names `fix` for change one with no gate recorded. The loop then lands both with nothing ejected, `aa.txt` is `AA` in change one's closed commit, and exactly one gate runs.
- **Fix round:** `cmd_land_fix` now lets a round opened by a stack that no reviewer has answered take the fix. Otherwise it opens round n+1 once the round has passed. The updated `test_land` case covers both.
- **Docs and the loop:** the land skill's `fix` and `close` text and `cmd_train`'s docstring now say the fix comes before the gate. 147's `train --run` loop follows the same reading. `test_train_run_makes_the_stored_fix_once` now expects one gate for change two instead of two.
- **Open questions in intent.md:** I did not check how the fix behaves on a change that conflicts when stacked. The code runs it after the resolution, because the `fix` check sits after the rebase handling. The second question, letting the person choose to fix after the gate, is not implemented. I read it as out of scope.

## Evidence
$ uv run --group dev pytest -q -n 4 tests/test_train.py tests/test_land.py -k "fix"
(tail) ......   [100%]
6 passed in 12.47s
exit: 0

$ ls .sdlc/work/154-landing-fix-before-gate/checks.md
ls: .sdlc/work/154-landing-fix-before-gate/checks.md: No such file or directory
exit: 1

$ git diff d708064fcf8a13421e8a350e4158e3bfff76b810...HEAD -- plugins tests
(read) diff of factory.py, land/SKILL.md, tests/test_land.py and tests/test_train.py, as summarised above
exit: 0

$ cat .sdlc/work/154-landing-fix-before-gate/build/land-1.gate.md | head -20
GATE: PASS … Command: ./check.sh … Exit: 0
exit: 0
