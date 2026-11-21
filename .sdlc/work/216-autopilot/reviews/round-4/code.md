VERDICT: PASS

Round 4 built the D8, D9 and D10 answers from `decisions.md`, and each is done. The gate record `build/round-4.gate.md` reads `GATE: PASS`. I read the code and the tests, and ran 9 named tests, which passed.

- **D8 (sensitive paths guarded):** `_default_guards()` (`autopilot.py:205`) adds the base branch's `[review] sensitive` paths to the policy and review docs and `irreversible`. It reads them from the base branch, so a change can't narrow its own guards.
- **D9 (seeds with an `Issue:` line):**
  - `sdlc.py status --json` items now carry `issues`.
  - `candidates()` (`autopilot.py:299`) takes a seed with an issue, or an unreadable `Issue:` line, only when `--seeds` names it.
  - `open_wave()` passes the issue numbers to `open_seed()`. `open_seed()` holds an unreadable seed before any agent runs and writes `closes:` otherwise, so the landing's `issue` signal and the issue close work again.
- **D10 (what `--by autopilot` protects):** the docs now say it guards against accidental inheritance, not against a same-user process that sets it on purpose.
- **Settled items hold:** `take_markers()` runs first in `main()`. So the host's check, `accept`, a train's tip gate and agent sessions never inherit either marker. Only `loop_env()` gives them back to a loop's own children. `sdlc.py status --json` exists, and a real, unstubbed test reads it.

## Notes
- NIT: `.sdlc/work/216-autopilot/spec.md`: R19 still gives the default guards as the docs plus `irreversible`, but D8 added `sensitive`. The spec should be brought in line with the ledger {docs S low}
- Done well: `candidates()`, `open_seed()` and `opened_intent()` treat an unreadable `Issue:` line as a hold rather than a guess. The new tests were run red first.
- Run: `tests/test_autopilot.py -k "sensitive_paths or issue or real_status or by_autopilot"`, 9 passed.
