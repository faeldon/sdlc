VERDICT: PASS

I ran the named tests for both fixes and all 31 passed. The change's code diff matches the spec's R1–R8 as far as I read it, and I found no failure.

## Notes
- **checks.md:** the change has none, so there was nothing to read or run.
- **Gate record:** the file opens with `GATE: PASS`. Attempt 1 failed, and a later attempt passed. I cited the record and did not rerun the gate.
- **Nits (R1–R3):** `named_nits()` now reads only ids on a `Nits taken in:` line in the Approach or Requirements. It accepts a plain line, a list item or a bold lead, and continuation lines. A line under `## Problem` retires nothing. The tests that cover this passed.
- **Fix already made (R5–R7):** `land-fix --commit` goes on with no dirty files only when the report gives `FIX: ALREADY MADE` and passes the `read_evidence()` check. It exits 0 with `fixed: []` and `already_made: true`, and keeps the ask file, so the fix still counts as a signal. It still refuses with no report, no claim or bad evidence. Edits outside the folder are amended as before. These tests passed.
- **Not run:** I ran only the selected tests for these paths, not the full suite or an end-to-end train. The spec's train test (R8) and the later spec items matched by `-k "nit or fix or marker"` are in the 31.

## Evidence
$ cd <path-to-clone>/.claude/worktrees/181-landing-nits-and-fixes; head -8 .sdlc/work/181-landing-nits-and-fixes/build/round-1.gate.md
GATE: PASS

## Attempt 1

Verdict: FAIL
Command: ./check.sh
Build: d98a52e0bcee7802
Exit: 1
(read; the gate record's first line is `GATE: PASS`.)

$ uv run --group dev pytest -q -n auto tests/test_land.py tests/test_train.py tests/test_prompts.py tests/test_skills.py -k "nit or fix or marker" 2>&1 | tail -5
31 passed in 18.00s
exit: 0

$ ls .sdlc/work/181-landing-nits-and-fixes/checks.md
ls: .sdlc/work/181-landing-nits-and-fixes/checks.md: No such file or directory
exit: 1

$ git diff 515322767ba6c63df44d70eb5bbe88ca6e86ba89...HEAD -- plugins/factory/scripts
(diff of factory.py and landing.py, read; as summarised above)
exit: 0
