VERDICT: CHANGES

- CHANGE: plugins/factory/scripts/factory.py:4246: when the server answers and then `proc.poll()` shows it has exited, `_up()` returns `True` (lost) without probing the port. That breaks the rule this round asked for: only a port that won't bind is lost. A server that answers and then dies on its own, while the port is free, gets three starts and a false "lost" record, the same bug the kept finding named. The fix: in that branch, return `(why, not _binds(host, port))`, so a port that binds reads as the server failing on its own. Add a test that drives `_up()` directly with a stub process whose `poll()` returns 1 after a listener on the port is closed, and asserts `lost` is False.

## Notes

- Note: the bind probe runs after the server has already exited, so a port a parallel run held and then released in that moment binds, and the try counts as the server's own failure, not retried. That is a narrow limit of the probe, not a defect in it.
- Nit: `_binds()` always opens an IPv4 socket, so a `[ui] url` host that is an IPv6 literal fails the bind and is counted as lost. Resolving the host with `getaddrinfo` (or taking the family from it) would make the probe match the host the server uses.

## What was done well

- The rework fixes the kept case as asked. A `serve` that exits 1 on a free port is started once, leaves no `retries` entry, and sets `problem`. `test_a_server_that_fails_on_its_own_is_started_once` pins this.
- `_serve()` clears `problem` at the start of each try and calls `_stop()` before deciding whether to retry, so a retry never inherits the last try's problem and no server is left running. A fresh fixture copy is still made per try.
- `_resolve()` and `read_verified()` are unchanged from round 1 and still pass their landing-round test.

## Tests and commands run

- `uv run --group dev pytest -q -n auto tests/test_factory.py tests/test_land.py tests/test_skills.py`: 608 passed. The six shot-related tests (`-k "lost or fails_on_its_own or landing_verifiers or shots"`) also pass.
- `uv run --group dev ruff check` and `ruff format --check` on `factory.py` and `test_factory.py`: clean.
- Not run: the full `./check.sh` gate and the Windows portable suite. The new port tests use real sockets and aren't marked `portable`.
