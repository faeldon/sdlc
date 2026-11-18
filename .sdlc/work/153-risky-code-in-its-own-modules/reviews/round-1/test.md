VERDICT: PASS

Every requirement from R1 to R10 has a test that fails without it. R11 and R12 have no test of their own, by design. I found nothing to change.

- **R1/R2:** `test_the_named_code_lives_in_its_module` is parametrized over both pairs and has the two by-name wrappers `test_close_push_and_the_lock_live_in_closing` and `test_the_landing_lives_in_landing`. It fails if a named entry is still defined in the script or missing from the module.
- **R3:** `test_the_line_between_script_and_module_holds` checks both directions: a named-or-not function the script reaches that should have stayed, and a script function that only the module calls and so should have moved. It also counts the calls `retro.py` and `board.py` make into `sdlc`, so a shared helper isn't wrongly flagged as only the module's.
- **R4:** `test_the_modules_are_loaded_by_path` checks for an import, a `sys.path` edit and exactly one `spec_from_file_location`. `test_the_modules_are_bound_live` asserts `closing.sdlc.__dict__ is vars(sdlc)`, and likewise for `landing`.
- **R5:** `test_the_modules_read_nothing_while_loading` walks decorators and default arguments but not function bodies, so it can fail on the `moves=` default.
- **R8:** `CORE` and `SCRIPTS` now list both modules. The two reach tests, `test_the_source_guards_reach_closing_py` and `test_the_work_path_guard_reaches_closing_py`, plant text and assert the guards find it.
- **R9:** `test_the_factory_never_loads_sdlc_py` covers both factory files.
- **R10:** `test_the_landing_code_is_reviewed_in_depth` reads the repo's real `[review]` list. Each module gives `full` with its path in `sensitive`; each script gives `light` with an empty `sensitive`; and `risk_paths` names both modules and neither script. `.sdlc/config.toml` already lists `scripts/closing.py`.
- **R6:** The edits under `tests/` that I read are changes of how a moved name is reached (`sdlc.closing.X`, `factory.landing.X`) or ruff reflow. I saw no expected value edited.

## Notes

The gate record `build/round-1.gate.md` is green: `2934 passed, 28 skipped in 111.51s`, with ruff, format and plugin validate passing. I ran `pytest tests/test_modules.py tests/test_factory.py::test_the_landing_code_is_reviewed_in_depth tests/test_sdlc.py::test_the_source_guards_reach_closing_py -q` and got 15 passed.

There is no `checks.md` in the change folder, so there are no acceptance checks to judge. R7's `--help` byte comparison is a build-evidence item that I couldn't verify from the tests.

- NIT: tests/test_sdlc.py:1921: the spec's `test_the_source_guards_reach_closing_py` plants all four cases (main ref, `gh` call, literal `work/`, second push). It plants only two, and the other two live in `test_work_folder.py` and presumably `test_skills.py`. {tests S low}
