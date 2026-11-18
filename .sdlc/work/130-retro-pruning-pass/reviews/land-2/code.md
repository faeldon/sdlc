VERDICT: PASS

The rebase left the change intact. Against the commit it was rebased onto, the diff to `.sdlc/work/inbox.md` removes only the `2026-11-17-87` pruning-pass seed, which is the seed this change builds. At that commit `2026-11-17-89` and `2026-11-18-1` were already absent, so the builder's inference about them was right and nothing of the base's was reverted.

I walked R1–R12 against the code, and each has code behind it:
- **Config (R1):** `COMMAND_LISTS` gains `test_times`.
- **Limits (R3):** `_evidence()` takes `timeout` and `limit` arguments, and `retro()` passes the 600 s and 5,000,000-character limits only for `test_times`.
- **JUnit read (R4):** `junit_times()` returns an error row and never raises. It never reports a time of 0.
- **Times block (R5, R6):** `_times()` gives `unset`, `failed` or `ok`. A truncated report is a failure, and no command output is kept.
- **Drift and `due` (R7–R9):** `drifted_tests()` matches the spec, and `_tests()` and `due` follow it. `UNMEASURED` has the two new signals.
- **Shared lookback (R8):** `_lookback()` is read once and passed to both the architecture and tests passes.
- **Skill and docs (R11, R12):** the skill and `REFERENCE.md` changes match what the spec names.
- **Context (pass 5):** the `AGENTS.md` Retrospectives line now names `retro.test_times`, and I found no context doc that has gone false.

The edge cases the spec names hold up:
- An `ok` state with no timed cases has no division by zero, because `total` is positive whenever `timed` is non-empty.
- Drift finds each test's last touch by walking the changes oldest first.
- With no base branch, `drifted` is `None`.

## Notes
- NIT: scripts/retro.py:1046: `lookback or _lookback(...)` would read better as `if lookback is None`. This repeats the earlier F5.
- NIT: AGENTS.md:139: the wrapped line `run), so \`retro\` is` is short and could be rewrapped. This repeats the earlier F6.
- NIT: docs/REFERENCE.md:103: the commands-`sdlc.py`-runs line now runs past the wrap width.
- Done well: `drifted_tests` and `junit_times` are pure and small, and the lookback rows are gathered once for both passes.
- I ran no tests or commands. I read the diff, the spec, `land-1.md`, the inbox diff and the base commit's inbox. The builder's `./check.sh` result in `land-1.md` (2,387 passed, 13 skipped) is unverified by me.
