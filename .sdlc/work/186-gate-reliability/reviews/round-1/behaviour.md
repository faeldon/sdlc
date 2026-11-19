VERDICT: PASS

## Notes
- The spec names no path, so I ran the tests the change touches. These are `tests/test_adoption.py` (13 passed) and the drawer test in `tests/test_board_browser.py` (1 passed).
- The new offline test in `test_adoption.py` has a name that matches its intent: with the index unreachable and nothing cached, it skips and names the network.
- I did not re-run the gate. Its record shows `GATE: PASS` with exit 0.
- Check "The drawer test bounds only a hang, never a poll's speed": I expect it to pass. The `page.set_default_timeout(PATIENT)` line appears once, and no `timeout=` appears in the file.
- I could not simulate a loaded gate or a downed network here. I checked those behaviours only by reading the code and its tests.
- `decisions.md` D1 is the builder's default of a 120s bound, which no one has answered. It matches the intent's "wait on state, not time", so I raised nothing.

## Evidence
$ cat .sdlc/work/186-gate-reliability/build/round-1.gate.md | head
GATE: PASS … Command: ./check.sh … Exit: 0
exit: 0

$ uv run --group dev pytest tests/test_adoption.py -q -rs
13 passed in 21.85s
exit: 0

$ uv run --group dev pytest tests/test_board_browser.py -q -rs -k drawer
1 passed, 1 deselected in 4.38s
exit: 0

$ grep -c 'page.set_default_timeout(PATIENT)' tests/test_board_browser.py
1
exit: 0

$ grep -c 'timeout=' tests/test_board_browser.py
0
exit: 1
