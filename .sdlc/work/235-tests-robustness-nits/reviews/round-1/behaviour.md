VERDICT: PASS

The change does what the spec says on the path I ran. Both the gate's record and my run of the named tests are green.

## Notes
- **`checks.md`:** the change has none, so I read no acceptance checks.
- **End-to-end path:** the spec names no single path. I ran the spec's Verification test list and the one user-facing behaviour change, `preflight --preview --nits`. It exits 1 with "only word ship's question, which --preview doesn't ask; run --question for it", as the spec's R-for-2026-11-21-30 describes. The `exit: 0` after it in the Evidence is `tail`'s status, not the script's.
- **Code hunks read:**
  - `uncarried()` now names a SETTLED but unticked default.
  - `origin_trailer()` and `fix_trailers()` catch only `(OSError, ValueError)`.
  - The upstream marker match is now `lstrip().startswith`.
  - `_read_hosts()` skips a listed path that a `!` line also excludes. This follows D1, which is still a default awaiting the person's confirmation.
  - The autopilot skill now says to single-quote a goal.
- **`entries.md`:** it holds 31 `Retire` lines, matching the intent's 31 nits.
- **Not run:**
  - I did not revert individual hunks to check that each named test fails without its fix.
  - I did not run `-m portable` or `./check.sh`. The gate record covers `./check.sh`.

## Evidence
$ head -8 .sdlc/work/235-tests-robustness-nits/build/round-1.gate.md
GATE: PASS
Verdict: PASS
Command: ./check.sh
Build: 1014392d9ac0f5c5
Exit: 0
exit: 0

$ uv run --group dev pytest -q -n auto <the spec's named test files> 2>&1 | tail -5
1507 passed, 1 skipped in 171.15s (0:02:51)
exit: 0

$ uv run --quiet --script scripts/sdlc.py preflight 235 --preview --nits 2>&1 | tail -3
⚠  preflight: --nits only word ship's question, which --preview doesn't ask; run --question for it.
exit: 0

$ grep -c "^Retire" .sdlc/work/235-tests-robustness-nits/entries.md
31
exit: 0

$ git diff HEAD --stat -- tests/prompts | tail -1
(no output: `tests/prompts` is unchanged)
exit: 0
