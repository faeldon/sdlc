I added the single test R10 asks for, `test_nothing_rewrites_decision_md`, and the full gate (`./check.sh`) passes with 2750 tests.

**The one kept change (C1): R10 had no single test.** The new test is in `tests/test_land.py`, not `tests/test_factory.py` as `plan.md` said, because that file already has a working `land-check` setup in a scratch repo. I updated `plan.md`'s R10 line to the new location.
- **What it does:** it builds an escalated change with one `gate` and one `look` reason. It then runs `decisions`, `ask`, `sdlc.py gate`, `land-check` and the board's state in turn. After each one it checks that `decision.md` is byte for byte what the approver wrote, and the failure message names the step.
- **Sanity check:** it passed on its first run, because nothing writes `decision.md`. To show it can catch a rewrite, I briefly made `ask` append a line to the file, and the test failed naming `ask`. I then put `factory.py` back from a copy taken just before; a search finds no trace of the line.

Nothing new in `notes.md`. I raised no decisions this round. Everything is still uncommitted, and `HEAD` is still `0710451`.

## Evidence

$ uv run --group dev pytest -q tests/test_land.py -k nothing_rewrites
1 passed, 76 deselected in 20.53s
exit: 0

$ uv run --group dev pytest -q tests/test_land.py -k nothing_rewrites   (with `ask` made to append to decision.md)
E           AssertionError: ask
1 failed, 76 deselected in 1.67s
exit: 1

$ grep -c 'open("a", encoding="utf-8").write("x' plugins/factory/scripts/factory.py
0

$ ./check.sh
All checks passed!
290 files already formatted
2750 passed, 28 skipped in 135.77s (0:02:15)
✔ Validation passed
✔ Validation passed
exit: 0

$ git log --oneline -1
0710451 Close 141-board-landing-track-truth
