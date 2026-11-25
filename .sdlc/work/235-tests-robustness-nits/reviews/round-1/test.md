VERDICT: PASS

I reviewed the change against the spec and the gate's record. I did not run any test myself.

## Notes

- **Gate:** `build/round-1.gate.md` is `GATE: PASS` on `./check.sh`: `4145 passed, 29 skipped in 218.84s`, and plugin validation passed.
- **Coverage:** every requirement from R1 to R29 has a test that fails without it. R3 and R5 are retirements and need no test. R30 is the gate itself.
- **Code fixes:**
  - R1: the new `settled` case reaches the new branch in `uncarried()`.
  - R2: the `TypeError` half of the test fails on the old `except Exception`.
  - R4: the third issue, with the marker on its second line, fails against the old `in` match.
  - R6: `--preview --nits` now exits 1, which the old code did not.
  - R7: `test_autopilot_single_quotes_the_goal` checks Steps 1 and 3.
- **Test-only nits:**
  - R10: `test_three(*, capsys)` is found only because `kwonlyargs` is now read.
  - R20: `_names()` and its portable test check whole-word matching.
  - R21: the `_hand_digests` and `_hand_hash` bodies are compared with the docstring dropped, as `test_windows.py` does.
  - R22: all four bind and TIME_WAIT combinations are covered.
  - R23: the fallback is tested through both copies.
  - R25: `os.replace` is recorded and the cache's bytes are checked for `\r\n`.
- **Retro change (R15):**
  - `_read_hosts()` now skips a listed path that a `!` line also excludes. That is a code change the spec did not list.
  - It is recorded as a default in `decisions.md` (D1, unticked) and is consistent with 208 R3. The person weighs it at landing.
  - The R14 and R15 test counts moved accordingly, `listed` 5 to 6 and `own` 1 to 2, and the retro report's "read of 6 listed" text changed with them.
- **`entries.md`:** all 31 ids are present. R3 (2026-11-21-8) is retired as `wontfix` and R5 (2026-11-21-20) as `stale`, each with its reason.
- **`checks.md`:** none exists, and none is needed. Every requirement is covered by a suite test.
- NIT: plugins/factory/skills/autopilot/SKILL.md:99: the reflowed Step 1 line is now well past the file's wrapping width {style S low}
