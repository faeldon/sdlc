I've fixed all three KEPT lines from round 1. The full gate passes: ruff is clean, 2005 tests pass, and plugin validation passes. Each new test failed for the expected reason before its fix.

- **code C1 (`reload_error` said to restart):** the message now reads "`board.py` changed but won't load (…): the board serves the code it had until the file loads". Without a restart, the board loads the file again the next time it changes. `test_the_running_board_serves_board_py_as_it_is_on_disk` now also checks the message never says "restart".
- **ux C2 (a problem only took precedence at a closed stage):** `next_action()` now returns "fix what its problems name" for any card with a `problems` entry, at every stage, as the comment already said.
  - `test_a_card_with_a_problem_never_names_close` now covers `shipped`, `dropped`, `build`, `test` and `plan`.
  - **One existing expectation changed:** card 004 has both an unreadable reply and a blocking decision. It now says "fix what its problems name" instead of "answer its decision in the factory's supervisor", matching its Needs you column.
- **ux C3 (a rebasing card told the person to build or ship):** a rebasing card now says "a rebase is stopped in its worktree: resolve its conflicts, then sdlc.py resolve NNN --continue, or sdlc.py resolve NNN --abort". These are the commands `skills/ship/conflict.md` names, and I confirmed `--abort` there. The rebase line comes before the problem line, because the conflicted files may be what won't read. `test_a_change_being_rebased_keeps_its_card` checks this line.

`plan.md` now describes the new order in `next_action()`. `docs/REFERENCE.md` (*The board*) now gives the rebasing card's next step and says a problem is the next step at any stage. Nothing is left in `notes.md`. I raised no new decisions this round; the two `[default]` decisions from round 1 still stand as assumed.

## Evidence

```
$ uv run --group dev pytest -q tests/test_board.py -k "never_names_close or being_rebased or on_disk or unreadable_reply"   (before the fix)
E       assert "answer its d...'s supervisor" == 'fix what its problems name'
E             + the factory is building it: wait for its decision
E       AssertionError: never ship or build mid-rebase
exit: 1

$ uv run --group dev pytest -q tests/test_board.py
55 passed in 32.27s
exit: 0

$ ./check.sh
All checks passed!
214 files already formatted
2005 passed in 92.28s (0:01:32)
✔ Validation passed
exit: 0
```
