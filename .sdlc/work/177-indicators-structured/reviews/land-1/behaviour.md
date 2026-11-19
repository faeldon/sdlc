VERDICT: PASS

The indicator path works as the intent describes. `.sdlc/function-heat.py` prints JSON rows (`name`, numeric `value`, `unit`). The indicator tests and the function-heat tests pass. The land-1 conflict resolution in `scripts/retro.py` kept both sides' `render_report` and `retro_report` changes, and `tests/test_retro.py` (189 passed) and ruff were green after it. I did not run the full `retro` command end to end. The report table and its trend column are covered only by the tests.

## Notes
- `checks.md` does not exist for this change, so there are no acceptance checks to read.
- The gate record `build/round-2.gate.md` shows a green gate. Its only warning is the factory plugin's missing icon, which the record says does not change the result.
- I did not run the whole suite myself; I ran only `tests/test_indicators.py` and `tests/test_function_heat.py`.

## Evidence
$ python3 .sdlc/function-heat.py 2>&1 | head -5
{"name": "scripts/sdlc.py::cmd_release", "value": 2, "unit": "commits"}
{"name": "scripts/sdlc.py::cmd_release", "value": 228, "unit": "lines"}
{"name": "scripts/sdlc.py::cmd_run_cases", "value": 2, "unit": "commits"}
{"name": "scripts/sdlc.py::cmd_run_cases", "value": 86, "unit": "lines"}
{"name": "scripts/sdlc.py::cli_status", "value": 2, "unit": "commits"}
exit: 0

$ uv run --group dev pytest -q tests/test_indicators.py tests/test_function_heat.py -n auto
75 passed in 38.57s
exit: 0

$ ls .sdlc/work/177-indicators-structured/checks.md
ls: .sdlc/work/177-indicators-structured/checks.md: No such file or directory
exit: 1

$ tail -5 .sdlc/work/177-indicators-structured/build/round-2.gate.md
    These plugin directory checks do not change the result below.

    The directory also runs a safety scan and a policy review that this command does not.
    ✔ Validation passed
exit: 0
