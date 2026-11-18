I've built the move: close, the push and the main lock now live in `scripts/closing.py`, and the factory's landing and train in `plugins/factory/scripts/landing.py`. The full gate passed: 2934 passed, 28 skipped, ruff clean, both plugins validate. Nothing is committed.

**How the move was done.** A throwaway script outside the repo moved each definition unchanged, with its decorators and the comments directly above it. It then fixed up each name that crossed the line: `sdlc.<name>` or `factory.<name>` inside the modules, `closing.<name>` or `landing.<name>` in the scripts. Scope is respected, so a local variable with the same name is left alone, and `ruff` showed no undefined names on either side. Which helpers move follows R3: a name moves when every piece of code that uses it has moved.

Edits beyond pure moving:
- `sdlc.py` gains `_load_closing()`, built like `_load_retro()`.
- `factory.py` gains its own `_Names` class and `_load_landing()`.
- `landing.py` runs `factory.FACTORY_SCRIPT` where it used `Path(__file__)`, so it has no path of its own (R5).
- `land_question()`'s `moves` now defaults to `None` and fills in the same default inside the body (R5).
- Six over-long lines were re-wrapped; the text they produce is unchanged.

**Tests added:**
- **`tests/test_modules.py` (new):**
  - R1/R2: the named code is defined in the module and not in the script.
  - R3: the line rule holds both ways.
  - R4: each module is loaded by path, never imported and without touching `sys.path`, and bound to a live view of its script.
  - R5: neither module reads anything while loading.
  - R9: `factory.py` and `landing.py` never import or load `sdlc.py`.
- **R8:** `closing.py` is added to `CORE` in `test_sdlc.py` and `test_work_folder.py`, to the push guard's sources, and to `SCRIPTS` in `test_windows.py` (which also gets `landing.py`). New tests check each guard still catches a planted `refs/heads/main`, a `gh` call, a literal `work/` path and a second push. The push guard now reads each file separately: joined together, retro's last function ran on into `closing.py`'s docstring, which mentions `_push()`.
- **R10:** `test_the_landing_code_is_reviewed_in_depth`. A diff touching either module gets full depth; one touching only `sdlc.py` or `factory.py` stays light; `risk_paths()` names both modules and neither script. With one listing removed from `config.toml` it failed (config then restored).
- **R6:** every other test edit only changes where a moved name is reached, including `setattr` targets. Some lines were re-flowed by `ruff format`, and the conflict-marker test now also reads the two new files. No expected value was edited.
- **R7:** `--help` for both scripts and the ten named commands is byte-identical to the base's. The before/after texts are in `/tmp/mv153`, which I compared with `diff -r`.

**Changes to `plan.md`:**
- **Constants rule.** A first pass moved constants by R3's rule alone and split families of constants that share one header comment: the `FACTORY_*` pinned copies, `BASE_REF`/`BASE_KEY`, `FRESH_RE`/`CASES_RE`, `ENTRY_RE`/`ENTRY_ID_RE`. Each header ended up on the wrong side. I redid it so a constant moves only when it is named or its whole commented block moves; otherwise it stays and the module reads it through the binding.
- **`RESOLVE_RECORDS` stays** in `factory.py`, because it is built at load time from names that stay.
- **The train's run block is named whole** (`RUN_UNDER_WAY`, `RUN_EJECTS`, `RUN_STOPS`, `RERUN`, `PUT_BACK` alongside `RUN_STEPS`), and its two section-header comments moved with it.

**Docs:** AGENTS.md (*Modules loaded by path*, *Closing*, *The factory*, the push rule), a row for each module in CONTRIBUTING.md's *Layout*, and a paragraph in the factory README's *Mechanism*. Nothing was left in `notes.md`.

**Who checks R11:** the build's first `verdicts` should return `depth: full` with both modules listed, because the base already lists them (158). That is the factory's run to check, not mine.

- DECISION: [default] Constants move only when named or when their whole commented block moves, not by R3's rule alone. Going ahead with this unless told otherwise.
  - OPTION: whole block or named — pinned-copy families and their header comments stay together, and the pin tests don't change; a few constants only moved code reads stay in the script
  - OPTION: R3's rule for constants too — matches R3's wording exactly; splits the pinned `FACTORY_*` family and three others, leaving header comments describing code that has gone
  - WHY: R3's test covers functions, and a split family is harder to review than a name read through the binding
- DECISION: [default] Close's measure step (`measure_change`, `fix_trailers`, `_factory_files`, `_agent_sessions` and their helpers) moves into `closing.py`, as R3's rule requires, since only close calls it. Going ahead unless told otherwise.
  - OPTION: move it — R3 holds as written; a change to the `Sdlc-*` trailers is now reviewed at full depth
  - OPTION: keep it in `sdlc.py` as a named exception — `closing.py` stays smaller; R3's test needs an exception list
  - WHY: R3's test demands it, and the trailers are written into the `Close` commit itself

## Evidence

$ uv run --group dev pytest -q tests/test_modules.py
12 failed, 1 passed in 1.10s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k reviewed_in_depth   (with `plugins/factory/scripts/landing.py` removed from `.sdlc/config.toml`, then restored)
FAILED tests/test_factory.py::test_the_landing_code_is_reviewed_in_depth - As...
1 failed, 358 deselected in 3.51s
exit: 1

$ uv run --group dev pytest -q -n 8 tests/test_modules.py tests/test_archive.py tests/test_push.py tests/test_cleanup.py tests/test_register_lands.py tests/test_release.py tests/test_bugs.py tests/test_windows.py tests/test_sdlc.py tests/test_work_folder.py tests/test_skills.py tests/test_nits.py tests/test_metrics.py tests/test_land.py tests/test_train.py tests/test_resolve.py tests/test_factory.py tests/test_board.py tests/test_hand_gate.py
FAILED tests/test_skills.py::test_only_the_named_steps_push - AssertionError:...
FAILED tests/test_metrics.py::test_a_superseded_default_is_counted_but_not_open
5 failed, 2145 passed, 28 skipped in 226.06s (0:03:46)
exit: 1

$ uv run --group dev pytest -q -n 8 tests/test_skills.py tests/test_metrics.py tests/test_modules.py
605 passed in 0.95s
exit: 0

$ diff -r /tmp/mv153/help-before /tmp/mv153/help-after
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 153
All checks passed!
286 files already formatted
2934 passed, 28 skipped in 125.74s (0:02:05)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_modules.py tests/test_factory.py::test_the_landing_code_is_reviewed_in_depth tests/test_sdlc.py::test_the_source_guards_reach_closing_py tests/test_work_folder.py::test_the_work_path_guard_reaches_closing_py tests/test_skills.py::test_the_push_guard_reaches_closing_py tests/test_skills.py::test_only_the_named_steps_push
18 passed in 6.76s
exit: 0

$ git grep -nE '^def (cmd_close|_main_lock|_push|_push_plan|_lock_depth)\b' scripts/sdlc.py; git grep -nE '^def (cmd_land|cmd_train|cmd_resolve|_run_loop)\b' plugins/factory/scripts/factory.py
(no output)
exit: 1
