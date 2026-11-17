All five fixes to the board are built and left uncommitted. The full gate (`./check.sh`) passes with 2005 tests. Because the change touches six files, I wrote `plan.md` before the code.

## What was built (each test was seen failing before the fix)

1. **A card with a problem no longer says "close"** (2026-11-17-23). In `next_action()`, a shipped or dropped change that has a problem now gets "fix what its problems name" as its next step. Test: `test_a_card_with_a_problem_never_names_close`.
2. **The step track only treats `decision.md` as a finished run at `test`, `shipped` or `dropped`** (nit 2026-11-17-22). These are the same stages the column already uses. A change put back to `build` now shows the step its record names. Test: `test_a_decision_counts_on_the_track_only_at_its_stage`.
3. **`board --port 0` prints the port it actually bound** instead of `:0`. Test: `test_board_on_port_0_prints_the_port_it_bound`.
4. **A change being rebased keeps its card, with a `rebasing` badge** (2026-11-17-30). `change_dirs()` now reuses the existing `_change_trees()`, which reads the branch from the rebase's own `head-name` file with read-only `git rev-parse --git-path`. `worktrees()` is unchanged. The page shows the badge as plain text. Tests:
   - `test_a_change_being_rebased_keeps_its_card` stops a real rebase on a conflict. It checks the card, that `change_dirs()` finds the folder, that git's status and HEAD are the same after reading, and that the badge goes after `--abort`.
   - `test_the_rebasing_badge_is_built_as_text`.
5. **A running board picks up changes to `board.py` without a restart** (2026-11-17-47).
   - Routing moved into a module function `route()`. On each request the server compares the file's modification time and, if it changed, loads it again.
   - If the new file won't load (half-written or broken), the board keeps serving the old code. `/state.json` then carries `reload_error`, and the page header shows "stale · …".
   - `test_the_running_board_serves_board_py_as_it_is_on_disk` runs a copy of the board from a temp folder. It edits the copy, then truncates it, then restores it, and checks what is served each time. `test_a_board_that_wont_reload_says_so_on_the_page` checks the page shows the warning.

**One existing test changed:** `test_a_decision_or_a_stop_overrides_the_record` now sets `stage: test` before expecting every step done, because fix 2 makes a decision at `build` no longer count. The docs (`docs/REFERENCE.md`, *The board*) gained a sentence each on the rebasing badge, `--port 0` and the reload.

**`plan.md`:** written before the code, then updated after it to match what was built: the reload keeps the latest working `route()` rather than the whole module, and the two page tests were added. Nothing was left in `notes.md`.

**One limit of the reload:** the request handler, which does the Host check and sends the response, belongs to the copy of `board.py` the server started with. So `route(root, path, notice)` is now a fixed interface between a running server and any reloaded file. A later change to that signature, or to the handler itself, still needs a restart. The `board.py` docstring says so.

- DECISION: [default] Reload `board.py` when it changes, or only mark the page stale? Options: reload; flag only. Going ahead with reload, keeping the old code and flagging the page when a load fails. Reason: the intent's constraint ("a module that fails to load keeps the old one and says so") already assumes a reload.
- DECISION: [default] Should `change_dirs()`, and so `status`, also see a change being rebased, or only the board? Options: both; board only. Going ahead with both, through `_change_trees()`, while `worktrees()` stays as it is so `base`, `close`, `resolve` and numbering are untouched. Reason: the intent's Affected section expects `change_dirs()` to find it, and a change dropping out of `status` mid-rebase is the same bug.

## Evidence

```
$ uv run --group dev pytest -q tests/test_board.py -k "never_names_close or only_at_its_stage or port_0"   (before the fix)
FAILED tests/test_board.py::test_a_card_with_a_problem_never_names_close - As...
FAILED tests/test_board.py::test_a_decision_counts_on_the_track_only_at_its_stage
FAILED tests/test_board.py::test_board_on_port_0_prints_the_port_it_bound - a...
3 failed, 1 passed, 47 deselected in 1.79s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py -k "rebas or overrides"   (before the fix)
E       KeyError: '029-draft-rebase'
2 failed, 1 passed, 50 deselected in 1.56s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py -k "on_disk or wont_reload"   (before the fix)
E       AttributeError: module 'sdlc_board' has no attribute '_load'
2 failed, 53 deselected in 2.31s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py
55 passed in 23.81s
exit: 0

$ ./check.sh
All checks passed!
206 files already formatted
2005 passed in 59.57s
✔ Validation passed
exit: 0
```
