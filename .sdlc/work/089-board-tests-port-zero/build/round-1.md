The fix is in and uncommitted. The gate passes with 1903 tests, and the board's tests passed 40/40 in each of three parallel runs.

**What changed** (one slice, test first):
- **Red:** I changed `tests/test_board.py` so `served` calls `board.serve(repo, 0)` and reads the port from `server.server_address[1]`. `_free_port()` and the `socket` import are gone. I also added host cases to `test_the_board_answers_three_gets_and_nothing_else`: `127.0.0.1:0`, `localhost:0` and a host with no port must get a 404, and `localhost:<bound port>` a 200. Four served tests then failed with `assert (404 == 200)`, because the host check was still set to port 0.
- **Green:** in `scripts/board.py`, `serve()` now binds first, then builds the handler from `_handler(root, server.server_address[1])`, the port it actually got. Its signature and return type are the same, and `_handler()` and `cmd_board()` are untouched. So a fixed `--port` behaves as before, which `test_a_second_board_reports_the_first_and_anything_else_is_refused` still covers.
- **The host check is no looser.** Only the bound port is answered; port 0 and a bare host are refused.

**Change folder:**
- `plan.md` is new: you asked for one even though this is Tier 1. It lists the files, the slice, which test proves each outcome, and that `git revert` undoes everything.
- `checks.md` is new, with one acceptance check: `_free_port` stays out of the board's tests and `served` binds port 0. It exits 0 now.
- Nothing went into `notes.md`.

**Open questions from the intent:**
- *Return the bound port, or have the caller read `server_address[1]`?* The caller reads it, so `serve()` keeps its return shape.
- `factory.py`'s own `_free_port()` is the other question; I'm raising it below.

**Not mine:** `.sdlc/work/inbox.md` was already modified in the worktree before I started (the conflict `conflicts.md` records). I didn't touch it.

- DECISION: [default] Should `plugins/factory/scripts/factory.py`'s `_free_port()` (the UI review's dev server) be fixed here or filed as its own seed? Options: this change; a seed of its own. Going ahead with a seed of its own, which I haven't filed: that server is an outside command given `{port}`, so it can't bind 0 itself. Fixing it needs a different design (retry, or let the command report its port), and it's outside this intent's Affected files.

## Evidence

$ uv run --group dev pytest -q -n auto tests/test_board.py   (fixture on port 0, before the fix)
FAILED tests/test_board.py::test_the_board_answers_three_gets_and_nothing_else
FAILED tests/test_board.py::test_a_second_board_reports_the_first_and_anything_else_is_refused
FAILED tests/test_board.py::test_a_shipped_change_waits_on_close_until_its_worktree_goes
FAILED tests/test_board.py::test_the_board_writes_nothing - json.decoder.JSON...
4 failed, 36 passed in 2.72s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py::test_the_board_answers_three_gets_and_nothing_else   (before the fix)
E       assert (404 == 200)
exit: 1

$ for i in 1 2 3; do uv run --group dev pytest -q -n auto tests/test_board.py; done   (after the fix)
40 passed in 2.72s
40 passed in 2.34s
40 passed in 2.34s
exit: 0

$ ./check.sh
All checks passed!
192 files already formatted
1903 passed in 64.35s (0:01:04)
✔ Validation passed
✔ Validation passed
exit: 0

$ ! grep -q "_free_port" tests/test_board.py && grep -q "board.serve(repo, 0)" tests/test_board.py
exit: 0
