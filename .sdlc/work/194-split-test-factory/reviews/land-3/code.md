VERDICT: PASS

The landing rebase left the change intact. The diff is a pure move of the factory tests, plus one comment fix in `factory.py`.

## Notes
- **Test names:** the sorted `def test_` names at `bc2124c` and in the new `tests/test_factory_*.py` files are identical, 282 on each side.
- **`portable` marks:** there are 50 before and 50 after, and no test file imports from the old `test_factory`.
- **File sizes:** the largest new file is `test_factory_loop.py` at 1,418 lines, under the 2,000-line limit.
- **Gate:** `build/land-3.gate.md` shows 3503 passed, 29 skipped, and plugin validation passed. I did not run the suite or any other test.
- **Comment fix:** the `factory.py` comment that named `tests/test_factory.py` now names `tests/test_factory_agent.py`. I did not check that the pin it describes sits in that file.
- **Nit -37:** no new assertion was added for it. Decision `D1` records this as an open default, so the person confirms it at ship. I didn't re-check it.
- **Done well:** the split follows the old section areas, the shared fixture lives in `conftest.py` and the shared helpers in a single `factory_helpers.py`.
