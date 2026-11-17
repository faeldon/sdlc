VERDICT: CHANGES

- CHANGE: scripts/board.py:720: the `reload_error` text tells the person to "restart it once the file is whole", but `current()` already reloads on the next change to the file, and `test_the_running_board_serves_board_py_as_it_is_on_disk` proves the server recovers with no restart. The message sends people to do unneeded work. Fix: say the board keeps serving the code it had and will reload once the file loads, e.g. "`board.py` changed but won't load (…): the board serves the code it had until the file loads".

- Notes:
  - scripts/board.py:687: `spec.loader.exec_module` goes through the bytecode cache. Python validates a cached `.pyc` by source mtime in whole seconds and by size, so an edit that keeps the same size and lands in the same second as the last compile can serve stale code, against the "serves `board.py` as it is on disk" outcome. The test's +2 s mtime jump hides this. Fix: read the source text and `exec(compile(text, str(path), "exec"), mod.__dict__)` in `_load()`, which skips the cache and also keeps a running board from writing `__pycache__` into the plugin.
  - scripts/board.py:710-716: a reloaded module that loads but raises inside `route()` or `state()` (a NameError on a request, say) still breaks the board: the handler errors and the page says it isn't answering. The spec's constraint covers only a load failure, so this may be out of scope. If you want it covered, catch exceptions around `answer(...)` in the handler, fall back to the previous `route`, and set `error`.
  - scripts/board.py:99 and scripts/sdlc.py:864 (`change_dirs()`, via `_change_trees()`): `state()` calls `_change_trees()` on every poll, and `_change_trees()` runs `git rev-parse --git-path` twice for every worktree not in its change list, the main checkout included. Each `/file` request also goes through `change_dirs()`. A few git calls per poll is small, but it is avoidable waste: `state()` could take `rebasing` from the same `_change_trees()` result that `change_dirs()` uses.
  - The inbox entry's `[building]` tag and the `Building in …` line are the documented way intent marks a seed (sdlc.py:146, REFERENCE.md:417), so they are fine as they are. The spec file is absent because this is Tier 1; I reviewed against `intent.md` and `plan.md`, and `decisions.md` D1 and D2 are `[default]` answers I reviewed against.

## Notes

What is done well:
- The rebase fix is a clean split: `worktrees()` is unchanged, so `base`, `close`, `resolve` and numbering are untouched, and `change_dirs()` gains the rebasing folder through `_change_trees()`. The test checks that git's status, HEAD and branch are the same after reading, and it aborts the rebase at the end.
- Outcomes 2, 4 and 5 each have a test that fails without the change, and the reload test covers the valid edit, the half-written file, and the recovery.
- The page builds the new badge and the stale status through `h()` and `textContent`, and `test_the_rebasing_badge_is_built_as_text` pins that.

What I ran:
- `uv run --group dev pytest -q -n auto tests/test_board.py tests/test_sdlc.py tests/test_hand_gate.py tests/test_windows.py tests/test_nothing_local.py`: 327 passed.
- `uv run --group dev pytest -q -n auto` (full suite): 2005 passed.
- `uv run --group dev ruff check scripts tests`: all checks passed. `ruff format --check scripts tests`: 46 files already formatted.

I did not run `./check.sh`, which also runs `claude plugin validate --strict`.
