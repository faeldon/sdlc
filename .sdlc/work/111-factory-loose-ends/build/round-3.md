I kept the retry approach and fixed the one open finding: deciding whether a failed UI server's port was "lost" now happens in one place. The full gate passes (2203 passed, 9 skipped). The work is uncommitted and HEAD is still `09a8622`.

D1 and D2 aren't ticked in `decisions.md`, so I treated D1 as still "retry". I took the first option from `decision-1.md`: one helper that every exit path in `_up()` calls, instead of patching another branch.

**Slices built**
- **`factory.py`, new `_lost(host, port)`.** It returns `not _binds(host, port)`, and its docstring says it is the only place a server's end is judged.
- **`factory.py`, `_up()` rewritten.** It now has one exit for a server that has ended. Whether the server stopped before answering or answered and then stopped, `_up()` picks the message and returns `_lost()`. The branch that always counted the port as lost, which round 2 missed, is gone. A timeout is still never counted as lost. The check in `_serve()` for a port that already answers before the server starts is left alone. That runs before any start, so it isn't an exit path.
- **`_serve()` docstring.** It names `_lost()` and says "won't bind once the server has exited, however it ended".

**Test added (it failed first, for the expected reason)**
- `test_a_port_is_lost_only_when_it_wont_bind_whichever_way_the_server_ended` calls `_up()` directly with a stub process. The stub reports itself running on the first poll, then exited with code 1.
  - Port freed: lost is False.
  - Port still held: lost is True.
  - Both runs check the exact "answered, but the dev server had exited 1" message.
- Before the fix it failed with `(True, 'port … answered, but the dev server had exited 1')`, which is the defect the verifier kept. The existing port tests still pass.

**Kept finding**
- KEPT `factory.py:4250-4251` (answered, then exited, returned `True` without checking the port): fixed through `_lost()` at the single exit, with the test above.

**`plan.md` changes**
- The retry entry now says only a port that won't bind is lost, for every way the server ends, decided by `_up()`'s one exit and `_lost()`.
- The Tests section lists the new test.

**README**
- The UI reviewers' paragraph now says what counts as a lost port, and that a server which fails on its own is started once.

**`notes.md`**
- The round-2 item is ticked, with a line saying how round 3 fixed it.
- I added a plain note (not a to-do) that retrying can't close the race completely. Another process can take the port between the "already answers" check and the server's own bind. That limit comes with the retry approach. Switching D1 to "report" would remove it, but each host's serve command would need to support a new placeholder.

**Still open**
- D1 and D2 are unconfirmed defaults; the person needs to confirm or change them.
- The port tests use real sockets and aren't marked `portable`, so CI's Windows job doesn't run them.

No new decisions this round.

## Evidence

$ uv run --group dev pytest -q tests/test_factory.py -k "lost_only_when"   (before the fix)
E           AssertionError: (True, 'port 49400 answered, but the dev server had exited 1')
1 failed, 207 deselected in 6.40s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k "lost or fails_on_its_own or shots"
6 passed, 202 deselected in 9.04s
exit: 0

$ ./check.sh
2203 passed, 9 skipped in 78.28s (0:01:18)
✔ Validation passed
exit: 0
