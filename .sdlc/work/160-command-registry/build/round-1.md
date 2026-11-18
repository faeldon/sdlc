I've built the change, uncommitted, and the full gate is green (2949 passed, 28 skipped). Every command in `sdlc.py` (42) and `factory.py` (31) now declares its own parser beside its handler, and both `main`s only parse and dispatch: `sdlc.py`'s went from 476 lines to 21, `factory.py`'s from 184 to 11. Top-level and per-command `--help` and the listed usage errors are byte-identical to the base, exit codes included.

**Slices**
1. **Tests first.** I wrote `tests/test_registry.py` (15 tests, marked `portable`) and ran it before any code: 14 failed as expected. `test_main_runs_a_stand_in_handler` passed even then, because `main` already reached handlers by their global names. It guards R7 rather than proving it.
2. **`sdlc.py`.**
   - The registry helpers (`UsageError`, `Command`, `COMMANDS`, `arg`, `exclusive`, `command`, `_parser`) and `HELP_ORDER` sit near the top.
   - Each command has a `cli_<name>` adapter right after its handler; `METRICS_HELP` is now a module constant.
   - `close`, `retro`, `retro-commit` and `board` are registered after `_load_board`. The board line `return _load_board().cmd_board(root, args.port)` is kept word for word.
   - `cases compare` with no run raises `UsageError`, and `main` turns it into the same `ap.error` as before.
3. **`factory.py`.**
   - It has its own copy of the helpers, pinned identical to `sdlc.py`'s by a test, and its own `HELP_ORDER`.
   - `STOPPED` moved above `cmd_verdicts` with its value unchanged.
   - The six landing commands are registered after `landing = _load_landing()`.
   - The `change_root` step stays in `main`.
4. **`checks.md`.** Two acceptance checks:
   - every command's help and the listed errors match the merge base's scripts, run under `sh`;
   - none of `closing.py`, `retro.py`, `board.py` or `landing.py` is in the diff.

   Both exit 0 and leave the tree unchanged. The first one caught a real slip while I was building (`config`'s help had lost its f-string), which I fixed.

**What the tests prove**
- R1: no parser is built outside `_parser`, and `main` has no `args.cmd ==` (zero in both scripts) and no command name.
- R2: 32 adapters in `sdlc.py` and 25 in `factory.py` call a single handler, and each sits right after it.
- R7: replacing a handler on either script reaches `main`.
- R9: every name in `READ_ONLY`, `ALLOW_RULES` and `OWN_SCRIPT_CMDS` is a registered command.
- R10: registering a name twice is refused, naming it.
- R11: `HELP_ORDER` names no command twice and only registered ones, and the help lists commands in that order.
- R12: the five shared helpers are identical in the two scripts.

**Changes to `plan.md`:** an *As built* section covering the `Command` class, where `STOPPED` and `METRICS_HELP` now sit, and the formatting fix to the spec below.

**`notes.md`:** nothing left.

**One edit outside the code:** `ruff format --check` also formats Python blocks inside Markdown. The approved `spec.md` (and its copy `runs/spec-draft.md`) had a line over 100 characters in its `main` sketch, so the gate failed on it whatever the code did. I let ruff wrap that one call; no words changed.

No existing test, skill, doc or loaded module is in the diff, and `HEAD` is unchanged.

No decisions raised.

## Evidence

$ uv run --group dev pytest -q tests/test_registry.py   (red step, before any code)
14 failed, 1 passed in 8.53s
exit: 1

$ bash /tmp/registry_build/compare.sh   (before the config fix)
DIFF: plugins/factory/scripts/factory.py --help
<     config              .sdlc/factory.toml over the defaults, as JSON
>     config              {CONFIG_FILE} over the defaults, as JSON
exit: 1

$ sh /tmp/registry_build/c0.sh   (checks.md: Help and usage errors match the base)
exit: 0

$ sh /tmp/registry_build/c1.sh   (checks.md: The loaded modules are not in the diff)
exit: 0

$ uv run --quiet --group dev pytest -q tests/test_registry.py
15 passed in 0.76s
exit: 0

$ uv run --quiet --group dev pytest -q -n auto tests/test_board.py::test_status_never_loads_the_board tests/test_preflight.py tests/test_modules.py tests/test_windows.py
108 passed in 9.68s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 160
All checks passed!
2949 passed, 28 skipped in 126.00s (0:02:05)
✔ Validation passed
✔ Validation passed
exit: 0

$ grep -c "args.cmd ==" scripts/sdlc.py plugins/factory/scripts/factory.py
plugins/factory/scripts/factory.py:0
scripts/sdlc.py:0

$ git diff dd5369f --stat -- tests/ scripts/closing.py scripts/retro.py scripts/board.py plugins/factory/scripts/landing.py
(no output)
exit: 0
