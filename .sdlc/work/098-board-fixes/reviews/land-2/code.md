VERDICT: PASS

I reviewed the whole diff against `main` (merge-base `6ae0834`, HEAD `f02c571`). Nothing in the rebase changed the code, and the branch sits directly on `main`. The work is uncommitted only in the `runs/` sessions and `build/land-2.gate.md`, none of it code.

The change has no `spec.md`, so I took the requirements from `intent.md`'s Outcome list and the tests `plan.md` names. Each of the five outcomes has code and a test that fails without it:

- Rebasing card kept: `state()` and `change_dirs()` through `_change_trees()`, with `test_a_change_being_rebased_keeps_its_card`.
- Problem never names close: `next_action()`, with `test_a_card_with_a_problem_never_names_close` and the `PRECEDENCE` pairs.
- Reload: `_Live` / `_load()` / `route()`, with `test_the_running_board_serves_board_py_as_it_is_on_disk`.
- Decision counts only at `test` or closed: `_progress()`, matching `column()`'s stages.
- `--port 0`: `cmd_board()`, with its own test.

## Notes

- **Stale bytecode on reload (optional).** `_load()` goes through `spec.loader.exec_module`, so a reload can read a `.pyc` written from a source of the same size in the same second. That is a narrow window, and the 2-second offset in the test avoids it. `decision.md` proposes `sys.dont_write_bytecode` as the fix, but that flag only stops writing. CPython's loader still reads an existing valid `.pyc` first. The fix that works is to compile the source text directly into the module's dict, which also stops the running board writing `__pycache__`. The first load in `sdlc.py` already goes through `exec_module`, so the write predates this change.
- **REFERENCE overstates the reload.** `docs/REFERENCE.md` says a change to the board "needs no restart". Only `route()` reloads, meaning the page, `/state.json` and `/file`. The handler, its Host check, `serve()` and `cmd_board()` stay as first loaded, and an edit to them reports `live` without taking effect. `board.py`'s own docstring says this correctly, so the REFERENCE sentence should say "its routes" and name what still needs a restart.
- **Extra git calls on every poll.** `_change_trees()` calls `worktrees()` and then runs `git worktree list` again, and it runs `git rev-parse --git-path` for every worktree that isn't a change, the main checkout included. `state()` calls it on each poll, every 2 seconds, and `change_dirs()` calls it on every status. Reusing the one `worktrees()` listing would remove a call. The cost is small unless the worktree count grows.
- **Register edits ride on this branch.** `.sdlc/work/inbox.md` on this branch removes the entries this change fixes and adds seeds 52–58. Ship's documented path does this (`skills/ship/SKILL.md`, around line 437), but AGENTS.md says an entry "never rides on a change's branch, where a drop would lose it." One of the two is wrong, and that's for the person to reconcile, not a change here.
- **The `--abort` wording** still doesn't say the resolved work is kept under `refs/sdlc/end/<branch>`. `notes.md` already carries it.

## What is done well

- `test_a_card_in_two_states_names_the_higher_ones_step` checks every pair of states that can overlap, by the full text of the step each names. That ends the order-of-checks churn the earlier rounds kept finding.
- `test_a_change_being_rebased_keeps_its_card` reads the card mid-rebase and then checks that git's status, HEAD and branch are unchanged.
- The reload keeps the last good `route()` on a failed load and surfaces the error on the page through `textContent`. Nothing is built from HTML strings.

## What I ran

- `UV_PROJECT_ENVIRONMENT=/tmp/…` with `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`, `uv run --frozen --group dev pytest tests/test_board.py`: 101 passed, 9 skipped. The worktree's status was unchanged afterwards.
- `build/round-3.gate.md` records `./check.sh` at exit 0 with the tree unchanged on `f02c571`, the current HEAD. I didn't rerun the full gate.
