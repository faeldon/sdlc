I've made the one KEPT change from round 1: a dev server that crashes on its own is now started once, not three times. The full gate passes (2195 passed, 9 skipped).

**C1 (code), `_up()` counted any early exit as a lost port: done.**
- **The fix:** when the server exits before answering, a new `_binds(host, port)` probe tries to bind the port and closes the socket straight away. The try counts as a lost port, and gets another port, only when that bind fails. If the port binds, the server failed for its own reason: it isn't restarted, nothing is added to `retries`, and the problem is its exit.
- **Docs:** I updated the docstrings of `_up()` and `_serve()`, and `plan.md`'s description of the retry and its test list.
- **New test:** `test_a_server_that_fails_on_its_own_is_started_once` uses a `serve` of `echo started >> file; exit 1`. It checks for one start, one port picked, empty `retries`, and "exited 1 before answering" as the problem. Before the fix it failed: the server was started three times.
- **Existing test:** as the verifier suggested, I reran `test_shots_take_a_new_port_when_theirs_is_lost`. Its port that is bound but not listening still doesn't bind, so it still counts as lost, and the test passes.

The first run of the two port tests took 42s, much slower than earlier. Timed on their own they take 2.4s and 0.3s, so the slowness came from the machine, not the tests.

No decisions were raised this round.

## Evidence

```
$ uv run --group dev pytest -q tests/test_factory.py::test_a_server_that_fails_on_its_own_is_started_once   # before the fix
E       assert ['started', '...d', 'started'] == ['started']
1 failed in 1.32s
exit: 1
```

```
$ uv run --group dev pytest -q --durations=3 tests/test_factory.py::test_a_server_that_fails_on_its_own_is_started_once tests/test_factory.py::test_shots_take_a_new_port_when_theirs_is_lost
2.36s call     tests/test_factory.py::test_shots_take_a_new_port_when_theirs_is_lost
0.32s call     tests/test_factory.py::test_a_server_that_fails_on_its_own_is_started_once
2 passed in 2.88s
exit: 0
```

```
$ ./check.sh
All checks passed!
251 files already formatted
2195 passed, 9 skipped in 87.11s (0:01:27)
✔ Validation passed
exit: 0
```
