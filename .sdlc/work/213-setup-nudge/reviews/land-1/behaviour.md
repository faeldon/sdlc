VERDICT: PASS

The change does what the spec says. The targeted tests pass, and in this repo `status` prints no `■ Setup` line and `update --hook` prints nothing, as the spec predicts.

## Notes
- The gate record `build/round-1.gate.md` says `GATE: PASS`. I did not rerun the full suite.
- There is no `checks.md` for this change, so no acceptance checks were read.
- I did not run the scratch-repo steps for the changed-default case (nudge shown, hook prints its line, then both clear after setup records). Tests cover them: the R2 and R6 tests in `tests/test_setup_lifecycle.py` and `tests/test_update.py` are among the 31 that passed.
- The code diff matches R1–R11:
  - `drift_pending()` is shared by `readiness` and `setup_nudge()`.
  - `setup_nudge()` runs `drift()` only when the record is older, and keeps the line if drift can't be read.
  - `hook_line()` prefers the release line, wraps the setup half so it never fails a session, and still returns nothing when read in place.
  - The skills, REFERENCE.md, the hook description and the docstrings are updated.

## Evidence
$ uv run --group dev pytest -q tests/test_setup_lifecycle.py tests/test_update.py tests/test_skills.py -k "nudge or hook or drift or setup_s_line or in_place or strict" 2>&1 | tail -5
31 passed, 506 deselected in 12.60s
exit: 0

$ uv run --quiet --script scripts/sdlc.py status | grep -c '■ Setup'
0
exit: 1

$ uv run --quiet --script scripts/sdlc.py update --hook
(no output)
exit: 0

$ head -3 .sdlc/work/213-setup-nudge/build/round-1.gate.md
GATE: PASS

## Attempt 1
exit: 0

$ ls .sdlc/work/213-setup-nudge/checks.md
ls: .sdlc/work/213-setup-nudge/checks.md: No such file or directory
exit: 1
