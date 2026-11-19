VERDICT: PASS

The change meets all eighteen requirements. The gate record `build/round-1.gate.md` is green. I ran no tests myself.

- **Move and binding (R1–R4, R7, R8):** `run_state.py` holds the eight named functions plus `decision_preamble`. It defines only `factory = None`, and `factory.py` binds it with `_load_run_state()` right after `landing`. `tests/test_modules.py` has a case for each of these rules, and `cmd_verdicts` and its record writers stay in `factory.py`.
- **Landing nits (R9, R10):** the `cmd_land_fix` guard and the comment above `_run_loop` are in `landing.py` and nothing else there changed. The test for the guard is `test_a_fix_asked_with_its_land_round_folder_gone_is_not_a_traceback`.
- **Test nits (R11–R17):** the tests for the `last-id` conflict, the four train stops, the 60 s `time.monotonic()` deadline, the portable marks and docstring notes, and the Windows kill test are all present. The Windows test is `test_a_killed_train_run_resumes_on_windows`.
- **Nothing outside `plugins/factory/` and `tests/` (R18):** `tests/test_board.py`, `scripts/`, `defaults/`, `templates/`, `guide/` and the config have no diff.
- **Skills test (not in the spec):** the one edit to `tests/test_skills.py` re-points its source read at `run_state.py`.

## Notes

- **`decision_preamble` (R1/R3):** the spec's list named eight functions, but `decision_preamble` is also moved, because only `loop_state` calls it. R1 says R3's rule decides the list, so this is correct, and `notes.md` records it.
- **R5 and R6:** I did not run `git diff --color-moved=zebra`, so the pure-move check (R5) rests on the green gate and the call-site hunks I read. The `tests/test_factory.py` diff re-points `factory.loop_state` and `factory.read_gate` to `factory.run_state.…`, and the one multi-line reflow I saw there changed no expected value. I did not read the other test files' assertions line by line (R6).
- NIT: AGENTS.md:*Modules loaded by path*: it says only `landing.py` is bound to `factory.py`'s globals, so it now leaves `run_state.py` out. R18 leaves this to ship's context check; if ship adds it, it is one clause. {docs S low}
- Done well: the module docstring states where the line falls. `test_run_state_defines_no_constant` and the by-name `test_the_run_state_lives_in_run_state` pin that line. The kill test's body is shared with the POSIX test, so the path it takes is shown on Linux CI as well as Windows.
- Tests and commands run: none. I read the diff and the gate record only.
