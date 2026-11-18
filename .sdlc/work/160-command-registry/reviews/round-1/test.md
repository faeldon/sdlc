VERDICT: CHANGES

- CHANGE: tests/test_registry.py:25: `HELPERS` leaves out `Command`, the class the registry stores in `COMMANDS` and that `_parser` and `command` depend on. `plan.md`'s "As built" says it is pinned by `test_the_registry_copies_match`, but nothing pins it. Add `"Command"` to `HELPERS`. `COMMANDS` and `HELP_ORDER` differ per script, so they stay out. Without this, a change to one copy of `Command` in `sdlc.py` passes R12.

## Notes

- NIT: tests/test_registry.py:104: `test_main_runs_a_stand_in_handler` already passed before the move (the plan says so). It guards R7 and would catch a later regression, but it never failed on the old code. Only the `config` command is stubbed, so an adapter that bound its handler at import time would be caught for that one command and no other. Stubbing one more, such as `status` with the default no-command path, would cover R5's `--all` default through `main()`. {tests S low}
- The `checks.md` check, "Help and usage errors match the base", would fail without the change. It compares the merge base's scripts with the change's scripts, which differ after the move, so a divergence shows up as a `DIFF:` line.
  - It covers every command's `--help` and exit code, every R4 error case, and `factory.py` with no command.
  - It does not cover `sdlc.py` with no command (R5's default `status`). The existing `status` tests cover that, so I'm not asking for more.
  - I expect it to pass. I did not run it, per the rules.
- The `checks.md` check, "The loaded modules are not in the diff", is a single `git diff --name-only` against the merge base, so it can fail and leaves the tree unchanged. I expect it to pass.
- Coverage by requirement:
  - R1, R2, R10 and R11 have a test that fails if the property breaks.
  - R9 asserts the permission lists name registered commands.
  - R12 is covered except for `Command`, as noted above.
  - R3, R4 and R5 are covered by the check.
  - R6, R8 and R13 are covered by existing tests, the gate and the second check.
- Run: the gate record `build/round-1.gate.md` shows `./check.sh` passing with `2949 passed, 28 skipped`. I ran `uv run --group dev pytest tests/test_registry.py -q -p no:xdist` and got 15 passed.
- `git diff main --stat` lists `tests/test_function_heat.py` and `tests/test_windows.py`, and the diff of `tests/` shows only deletions. I read these as commits on `main` that landed after this branch, not as this change's edits, since the change only adds `tests/test_registry.py` (untracked). Worth confirming at landing.
