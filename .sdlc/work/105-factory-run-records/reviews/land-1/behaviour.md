The full output shows I misreported one result. My earlier "portable" line was actually the `test_skills.py` output.

The real portable run was the last command in the chain. It gave `296 passed, 9 skipped, 1829 deselected in 82.17s`, and the whole chain exited 0. My earlier `sleep`-and-`tail` read picked up the `test_skills.py` lines instead.

The verdict does not change.

VERDICT: PASS

## Notes
- All five test groups passed (16, 10, 3, 348 and 296 passed). The portable run also skipped 9 tests and deselected 1829 others.
- There is no `checks.md` for this change, so there were no acceptance checks to read.
- I did not run the new commands by hand against a real run. The tests cover them.
- The gate record `build/round-1.gate.md` says `GATE: PASS`. I did not run the gate again.

## Evidence
$ uv run --group dev pytest -q tests/test_factory.py -k "spec_draft or write_spec or supersed or decisions"
16 passed, 178 deselected in 72.79s
exit: 0

$ uv run --group dev pytest -q tests/test_sdlc.py -k "first_build or unfilled_plan"
10 passed, 204 deselected in 0.70s
exit: 0

$ uv run --group dev pytest -q tests/test_board.py tests/test_metrics.py -k "supersed or copies"
3 passed, 223 deselected in 0.33s
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py
348 passed in 0.40s
exit: 0

$ uv run --group dev pytest -q -m portable
296 passed, 9 skipped, 1829 deselected in 82.17s
exit: 0
