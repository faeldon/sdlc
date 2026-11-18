VERDICT: PASS

The change meets R1–R12 as far as I checked, and I found nothing that needs rework. I didn't read every line of the moved code or the full test diff.

## Notes
- Gate record `build/round-1.gate.md` is PASS, and I ran `tests/test_modules.py` on its own: 13 passed.
- `.sdlc/config.toml` already lists `scripts/closing.py` and `plugins/factory/scripts/landing.py` under `[review] sensitive`, with a comment saying why (R10, R11).
- `closing.py`'s docstring covers the contract R12 asks for. It names the rule for what moves, the binding, the sensitive listing and the invariants it keeps.
- The test diff I scanned is only reaches to the moved names (`sdlc.closing.X`, `factory.landing.X`) plus line rewraps. I saw no changed expected value (R6).
- `AGENTS.md` now places close, the lock and `_push()` in `closing.py`.
- Tests added: the line-between-script-and-module test, and the depth test that reads this repo's own `[review]` table.
- Not verified: the `--help` byte-identity check from R7, and the new `CONTRIBUTING.md` *Layout* rows.
