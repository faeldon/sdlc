- KEPT: code: C1: plugins/factory/scripts/factory.py:4225: `_binds()` reads a port held by a wildcard (0.0.0.0) listener as free on macOS, so a server that lost its port to a parallel run is judged "failed on its own" and not retried. It should also probe `(0.0.0.0, port)` with `SO_REUSEADDR`, and a POSIX test with a real wildcard listener should cover it.

## Notes
- I ran a scratch Python check on this machine (macOS). A listener on 0.0.0.0:P with `SO_REUSEADDR`: a probe on 127.0.0.1 with `SO_REUSEADDR` binds, so the port reads as free. A probe on 0.0.0.0 fails. This matches the claim.
- `grep` finds no wildcard probe anywhere in `factory.py`, so the defect is present in the code as it stands.
- The TIME_WAIT test (tests/test_factory.py near line 3289) is the one to re-run after the fix. I did not run it. I believe a wildcard probe with `SO_REUSEADDR` also tolerates TIME_WAIT, but the builder must confirm that.
