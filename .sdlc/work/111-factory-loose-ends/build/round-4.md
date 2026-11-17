I fixed the one kept finding: the port probe used by `_up()` no longer reports a freed port as held, so a server that answered and then exited on its own isn't recorded as having lost its port. The full gate passes (2204 passed, 9 skipped). The work is uncommitted and HEAD is still `09a8622`.

- **KEPT `factory.py:4225` (a port in TIME_WAIT reads as held):** `_binds()` now sets `SO_REUSEADDR` on its probe socket before binding, but only on macOS and Linux. On Windows that option would let the probe bind a port another socket holds, and TIME_WAIT doesn't block a bind there, so it stays off. The docstring says this.

**Test added (it failed first, for the expected reason)**
- `test_a_server_that_answered_and_closed_first_has_not_lost_its_port` makes a real connection that the server side closes first. The test checks the client read the close, which leaves the server's port in TIME_WAIT. It then runs `_up()` with a stub process that runs once, frees the port and exits with code 1. It asserts the exact "answered, then exited" message and that `lost` is False.
- Before the fix it failed with `assert True is False`, the bug the reviewer found.
- My first version of this test passed before the fix, so it proved nothing. `_answers()` closes its own connection at once, so the client closed first and the server's port never reached TIME_WAIT. I rewrote the test to make its own connection that the server closes first.
- The tests where another socket holds the port, listening or bound only, still pass. So a port that's really held still reads as held.

**`plan.md`**
- The retry entry says `_binds()` uses `SO_REUSEADDR`, and why not on Windows.
- The Tests section lists the new test.

**`notes.md`**
- Added a round-4 note on the fix and why Windows is excluded. The Windows branch isn't tested: the port tests use real sockets and aren't marked `portable`, so CI's Windows job doesn't run them.

No new decisions this round. D1 and D2 are still defaults the person hasn't confirmed.

## Evidence

$ uv run --group dev pytest -q tests/test_factory.py -k "closed_first"   (before the fix)
E       AssertionError: port 51447 answered, but the dev server had exited 1
E       assert True is False
1 failed, 208 deselected in 0.25s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k "closed_first or lost or fails_on_its_own or shots"
7 passed, 202 deselected in 4.04s
exit: 0

$ ./check.sh
2204 passed, 9 skipped in 57.98s
✔ Validation passed
exit: 0
