VERDICT: CHANGES

- CHANGE: plugins/factory/scripts/factory.py:4225 (`_binds()`): on macOS, a port held by a wildcard listener (a dev server bound to 0.0.0.0, as `python -m http.server` and `vite --host` do) reads as free. The probe binds only `host` with `SO_REUSEADDR`, and that bind succeeds while the wildcard listener holds the port. So a server that exits because a parallel run took the port is judged "failed on its own", is not retried, and the spec's retry requirement misses that case. Scratch checks on this machine (listener on 0.0.0.0:P, probe on 127.0.0.1 with `SO_REUSEADDR`) gave `True`, so the port reads as free. The probe on 0.0.0.0 with the option gave `False`, and the probe on 127.0.0.1 gave `False` for a 127.0.0.1 listener. Fix: `_binds()` reads the port as held if either `(host, port)` or the wildcard `(0.0.0.0, port)` fails to bind, both with `SO_REUSEADDR` on POSIX. Add a test on POSIX: a real listener on the wildcard, `[ui] url` on 127.0.0.1, `serve` exits; expect `lost` True, one retry recorded, and a fresh port on the last try. I have not checked that TIME_WAIT on the host address stays harmless for the wildcard probe, so the TIME_WAIT test must still pass with the change.

The land-1 conflict resolution is correct. The `inbox.md` diff against `main` removes only seeds 19, 64, 67 and 80, and the base's 81–88 are kept. Nothing else in the rebase touched code, so the finding above is in code that round 4 passed. I raise it anyway because you asked for the whole diff against `main`, and round 4's TIME_WAIT check only covered the same-address holder.

## Notes

- Nit (left over from round 1): the lines in AGENTS.md's *Writes before a WAIT* paragraph, `build/SKILL.md`'s `ui` sentence, and README's *Built on current code* bullet still run well past ~100 columns.
- Note: `_binds()` is still a macOS-only check for the TIME_WAIT case. Linux and Windows are not exercised here, and the new port tests aren't `portable`.

## What was done well

- Each of the four seeds is handled in the change it names, and the inbox removal matches that exactly.
- `_lost()` is the one place a serve's end is judged, and every exit path calls it.
- `_serve()` stops the server before deciding on a retry, and makes a fresh fixture copy per try.

## Tests and commands run

- `uv run --group dev pytest -q -p no:cacheprovider tests/test_factory.py -k "lost or fails_on_its_own or landing_verifiers or shots or serve or fresh or land"`: 16 passed, 193 deselected.
- `uv run --group dev pytest -q -p no:cacheprovider tests/test_land.py tests/test_skills.py`: 401 passed.
- Two scratch socket probes in `/tmp`, run with `python3 -I` and removed afterwards. Nothing in the repo was written.
- Not run: the full `./check.sh` gate (the builder's gate and the earlier round's run both passed), ruff, or the Windows portable subset.
