VERDICT: PASS

I read the diff against R1–R11 and the gate record, `build/round-1.gate.md`, which is PASS. I did not run any tests myself.

- **R1–R5, `setup_nudge()`:** each requirement has code and a test.
  - The nudge runs `drift()` only when the recorded version is older, and shares `drift_pending()` with `readiness`.
  - `OSError` or `ValueError` from `drift()` keeps the version line.
  - The R5 test shows the line for a non-UTF-8 review doc, and again with `drift` patched to raise.
- **R6–R8, the hook:** `hook_line()` works out the release line first. Setup's half sits in its own `try`, and the in-place and no-repo returns stay first. The tests cover the setup line, the release line winning, and a raising `setup_nudge` printing nothing with exit 0.
- **R9, R10:** `test_check_strict_ignores_drift` now builds a stale record with drift pending. The `status` and `intent` skills each name `■ Setup`, and the test covers both.
- **R11, docs:** REFERENCE.md, AGENTS.md, FEATURES.md, `hooks.json` and the three docstrings are updated and match the code.
- **Contract:** the change adds no write and no new subprocess. `D1` (the hook now runs drift's local reads while a record is behind) is an open default the person can accept at ship.

## Notes
- NIT: AGENTS.md:218: the reflowed *Setup* paragraph leaves a short line, "same change. `git.attribution` has no default on", that could be rewrapped. {style S low}
- Done well: `drift_pending()` is one shared rule, so setup can't say `complete` while status still sends the person to it. The tests follow the bug's own steps on the setup fixture.
- Ran: nothing. I read the gate record only.
