- KEPT: code: C1: plugins/factory/scripts/factory.py:4225: `_binds()` binds without `SO_REUSEADDR`, so a port in TIME_WAIT after a real connection reads as held and `_up()` returns a false `lost`; set `SO_REUSEADDR` on the probe socket and add a test that uses a real connection the server closes first

## Notes
- I read `_binds`, `_lost`, `_up` and `_answers`. `_binds` makes a plain `socket.socket()` and calls `bind` with no `SO_REUSEADDR`.
- I ran a throwaway Python check on this machine (macOS). After a listener accepted a real connection and closed it, then closed the listener, a plain `bind` on that port failed with `Address already in use`. It failed the same way when the client closed first.
- I did not run the `SO_REUSEADDR` variant or the repo's tests, so the claim that a port another socket holds still reads as held is the change's own check, not mine.
- `_up()` returns `_lost(...)` after an answered-then-exited server. In that case the TIME_WAIT port can read as held, so the false "lost" and the extra starts are reachable.
- I did not look at the existing round-3 test.
