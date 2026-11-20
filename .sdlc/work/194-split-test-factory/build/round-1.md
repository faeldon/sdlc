I split `tests/test_factory.py` into seven files, one per area of `factory.py`, plus a shared helper module. All 396 test ids are collected as before, with the same names and the same 98 `portable` marks, and the new files pass. The full gate passed: 3,438 passed, 29 skipped. Nothing is committed.

**Slices built**
1. **Plan.** `plan.md` is written. While reading I found the old file only ever held `factory.py`'s tests: the tests for `landing.py` and `run_state.py` were already in `tests/test_land.py` and `tests/test_train.py`. So I split it by area within `factory.py` instead of one file per module, following the old file's own section banners.
2. **The move.** I recorded the collected ids first, then split the file with a throwaway script kept outside the tree. Each test and helper moved unchanged and in its original order:

   | File | Lines |
   |---|---|
   | `test_factory_loop.py` | 1,409 |
   | `test_factory_decisions.py` | 1,301 |
   | `test_factory_agent.py` | 1,042 |
   | `test_factory_gate.py` | 987 |
   | `test_factory_depth.py` | 615 |
   | `test_factory_ui.py` | 492 |
   | `test_factory_eval.py` | 256 |

   - **Shared helpers.** Anything used by more than one file, plus `factory` and `sdlc` loaded once by path, is in `tests/factory_helpers.py`. Files import it the way they already import `train_driver.py`. Helpers used by a single file stay in that file.
   - **The `claude` fixture.** It and its `FAKE_CLAUDE` script moved to `tests/conftest.py`, so no file imports a fixture by name.
   - **Banners.** Every section banner stayed with its section. Four areas that began mid-section got a banner of their own.
3. **Proof of the move.**
   - The sorted id lists, all and `portable`, match the baseline exactly.
   - Every top-level definition parses to the same AST as in the old file: nothing missing, nothing extra, nothing different.
   - The one comment in `factory.py` that named the old file now names `tests/test_factory_agent.py`.

**Tests added:** none, because this is a move. `checks.md` has one acceptance check: the old file is gone, none of the seven files passes 2,000 lines, each one imports `factory_helpers` and none loads `factory.py` itself, and the `claude` fixture is in `conftest.py`. It exits 0.

**Named tests run:** the seven new files (396 passed), and `test_nothing_local`, `test_windows` and `test_modules` (84 passed).

**`plan.md`:** I added the banner handling, the AST comparison and the acceptance check after writing it.

**`notes.md`:** nothing left there.

**Nit 2026-11-19-37 is already covered.** `tests/test_land.py::test_a_landing_records_each_step_it_takes` already runs `land-review` through `cmd_agent` and asserts the row's `land` is 1 and that it has no `round`. That assertion came in after the nit was raised, so I wrote no duplicate. The intent's expected extra assertion therefore doesn't exist, and the test count is the same as before.

- DECISION: [default] Treat nit 2026-11-19-37 as already met by `test_land.py::test_a_landing_records_each_step_it_takes` and retire it with this change, adding no duplicate test. Going ahead unless told otherwise.
  - OPTION: retire it as met — no duplicate assertion; the intent's "apart from the new assertion" doesn't happen
  - OPTION: add a second, factory-only test in `test_factory_agent.py` — matches the intent's wording; it duplicates coverage and needs a whole landing set up to reach a landing round
  - WHY: the nit's exact ask (a `land-review` row from `cmd_agent` carries `land`) is already asserted word for word
- DECISION: [default] Split `factory.py`'s tests into seven area files rather than one file per module. Going ahead unless told otherwise.
  - OPTION: seven area files — each under 1,500 lines and following the old banners; more files to look across
  - OPTION: one file per module — the old file holds only `factory.py`'s tests, so it would stay one 6,000-line file, past the 2,000-line limit
  - WHY: the intent's 2,000-line outcome, and its own open question allows a split by area

- UNTESTABLE: none

## Evidence

$ uv run --quiet --group dev pytest --collect-only -q tests/test_factory_*.py | grep "::" | sed 's/^tests\/test_factory_[a-z]*\.py:://' | sort | diff /tmp/s194/before.txt - && uv run --quiet --group dev pytest --collect-only -q -m portable tests/test_factory_*.py | grep "::" | sed 's/^tests\/test_factory_[a-z]*\.py:://' | sort | diff /tmp/s194/before_portable.txt - && echo SAME
SAME
exit: 0

$ python3 /tmp/s194/same.py
missing [] extra []
differ []
exit: 0

$ uv run --quiet --group dev pytest -q -n 4 tests/test_factory_loop.py tests/test_factory_decisions.py tests/test_factory_depth.py tests/test_factory_eval.py tests/test_factory_agent.py tests/test_factory_gate.py tests/test_factory_ui.py
396 passed in 23.30s
exit: 0

$ uv run --quiet --group dev pytest -q -n 4 tests/test_nothing_local.py tests/test_windows.py tests/test_modules.py
84 passed in 1.68s
exit: 0

$ uv run --quiet --group dev ruff check . && uv run --quiet --group dev ruff format --check .
All checks passed!
319 files already formatted
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 194
3438 passed, 29 skipped in 197.27s (0:03:17)
✔ Validation passed
exit: 0

$ sh -c "$(sed -n '/^```sh$/,/^```$/p' .sdlc/work/194-split-test-factory/checks.md | sed '1d;$d')"
exit: 0
