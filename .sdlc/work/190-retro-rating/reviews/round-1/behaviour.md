VERDICT: PASS

The end-to-end path does what the spec says. `retro --report` with no draft prints an `## Experience` section with the right table and the "Not rated" line. The 30 new-feature tests pass. The gate's record is green.

## Notes
- `checks.md` does not exist for this change, so there are no acceptance checks to read.
- `drift` reports `breaking: []` and `refresh: []`, so setup's record matches what ships (R15). Its command exited 1, which I did not investigate. I printed only the top of its output.
- I did not run the full suite; I cite the gate's record instead.
- I ran no scenario with a rating draft present beyond the named tests.

## Evidence
$ head -5 .sdlc/work/190-retro-rating/build/round-1.gate.md
GATE: PASS

## Attempt 1

Verdict: PASS
exit: 0

$ grep -n "exit\|passed\|failed" .sdlc/work/190-retro-rating/build/round-1.gate.md | head
62:    3534 passed, 29 skipped in 170.02s (0:02:50)
80:    ✔ Validation passed
94:    ✔ Validation passed
exit: 0

$ uv run --group dev pytest -q -k "experience or rating or aim_keys or two_question" tests/test_retro.py tests/test_skills.py tests/test_metrics.py
30 passed, 882 deselected in 12.37s
exit: 0

$ uv run --quiet --script scripts/sdlc.py retro --report | grep -n -A8 "Experience"
60:## Experience
62:| Figure | Value | Last retrospective | Trend |
64:| How working with the process felt (1 to 4) | — | — | unknown |
66:Not rated: the person gave no rating at this retrospective's question.
exit: 0

$ uv run --quiet --script scripts/sdlc.py drift | head -12
{ "base": "manifest", "version": {"manifest": "1.10.0", "plugin": "1.10.0"}, "breaking": [], "refresh": [], "report": [], ... }
exit: 1

$ ls .sdlc/work/190-retro-rating/checks.md
ls: .sdlc/work/190-retro-rating/checks.md: No such file or directory
exit: 1
