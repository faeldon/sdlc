VERDICT: PASS

The split is a faithful move, and nothing in it needs rework.

- **Count:** the old file and the seven new ones each hold 279 `def test_` functions, and the sorted name lists are identical.
- **`portable` marks:** 50 `pytest.mark.portable` decorators before and 50 after (16+10+5+0+4+15+0 across the new files).
- **Test run:** I ran the seven new test files with `tests/test_windows.py` and `tests/test_nothing_local.py`. 449 tests passed. I did not run the whole suite; the gate record covers that.
- **Gate record:** `build/round-1.gate.md` reads `GATE: PASS`.
- **File sizes:** the largest new file is `test_factory_loop.py` at 1,418 lines, well under the 2,000-line limit.
- **Shared fixture:** `claude` and `FAKE_CLAUDE` now live in `conftest.py`, and a single `factory_helpers.py` holds the shared helpers.
- **Stale references:** the one comment in `factory.py` that named `tests/test_factory.py` now names the file that pins it. The only other mention is a historical row in `docs/RETRO-SCORECARD.md`.
- **Context pass:** no context doc says anything false after this diff, so there is no `[context]` finding.

## Notes
- **Nit -37:** the intent asks for a new assertion, but the builder retired the nit as already met. `D1` in `decisions.md` records this as an open default. `tests/test_land.py::test_a_landing_records_each_step_it_takes` is cited as already asserting that a landing row from `cmd_agent` carries `land`. I did not open that test to check it. The count the gate collects therefore stays unchanged, which the intent allowed. The person should confirm `D1` at ship.
- **Seven files, not one per module:** `D2` records the other default, seven area files. The old file held only `factory.py`'s tests, so one file per module would have stayed over the 2,000-line limit. That choice is sound.
- **Done well:** the split follows the old section banners, and a mechanical AST comparison backs it up.
- **Commands run:** the test command above, plus `grep`/`diff` comparisons of the test names and `portable` marks against `HEAD`.
