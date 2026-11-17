VERDICT: CHANGES

- CHANGE: plugins/factory/scripts/factory.py:4225: `_binds()` binds without `SO_REUSEADDR`, so a port a server just answered on, and that the server closed first, is still in TIME_WAIT and reads as held. I checked this on this machine: after a server answers and closes its side first, a plain bind on that port fails with `Address already in use`, and the same bind with `SO_REUSEADDR` succeeds. So `_up()` returns `lost=True` for a server that answered, then exited on its own with its port free, which is the false "lost" record and three starts the last round asked to remove. The fix: set `SO_REUSEADDR` on the probe socket before `bind`. I checked that this still reports a port another socket holds as held, both listening and bound-only, so the existing `_held()` tests still hold. Add a test where the server answers over a real connection that the server closes first, then exits with the port free, and asserts `lost` is False; the current round-3 test closes the held socket without any connection, so it never reaches TIME_WAIT.

## Notes

- The kept finding is fixed: `_up()` returns `_lost(host, port)` in the answered-then-exited branch as well as the never-answered one, and `test_a_port_is_lost_only_when_it_wont_bind_whichever_way_the_server_ended` drives it with a stub that frees the port and asserts `lost` is False.
- The settled finding is also fixed: `test_a_server_that_fails_on_its_own_is_started_once` passes, with one start, no `retries` entry, and `problem` set.
- I checked the TIME_WAIT behaviour on macOS only. Linux also refuses a bind on a port with TIME_WAIT connections unless `SO_REUSEADDR` is set, but I did not run that here. The new test would settle it on both.
- Nit, not raised again since it was already noted last round: `_binds()` always opens an IPv4 socket, so an IPv6 `[ui] url` host is judged by the wrong family.

## What was done well

- `_serve()` clears `problem` on each try and calls `_stop()` before deciding whether to retry, so no server is left running and no try inherits the last one's problem.
- The probe is a single helper, `_lost()`, that every way of ending calls, so no branch decides on its own.

## Tests and commands run

- `uv run --group dev pytest -q -p no:cacheprovider tests/test_factory.py tests/test_land.py tests/test_skills.py -k "lost or fails_on_its_own or landing_verifiers or shots or serve"`: 9 passed, 600 deselected.
- Two scratch scripts in `/tmp` (since removed) checked the TIME_WAIT and `SO_REUSEADDR` behaviour with `python3 -I`. Nothing in the repo was written.
- Not run: the full `./check.sh` gate, ruff, and the portable (Windows) subset.
