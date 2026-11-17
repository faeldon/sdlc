VERDICT: PASS

The behaviour I could run holds. I read the spec only through `intent.md`, so I did not compare the changes to spec R1–R13 line by line. The diff after the rebase has no conflict. The gate record `build/land-1.gate.md` is green. The tests that pin each outcome pass, and none of the seeds the change fixes is left in `inbox.md`.

## Notes
- `checks.md` does not exist for this change, so there are no acceptance checks to read.
- I ran only the two test files named in the intent. I did not run a live factory landing, since that is a paid model run.
- Seeds 71, 72, 73, 74, 78 and 79 are all gone from `.sdlc/work/inbox.md`. Seed 77, which is the change's `idea:`, is gone too. That matches the intent's outcome that a seed its ship deleted stays deleted.
- Two untracked files sit in the worktree: `build/land-1.gate.md` and `runs/reviewer-behaviour.sessions`. They are run records, not code.

## Evidence
$ uv run --group dev pytest -q -n auto tests/test_land.py tests/test_factory.py
253 passed in 16.91s
exit: 0

$ tail -15 .sdlc/work/109-landing-stops-only-for-cause/build/land-1.gate.md
Validation passed (plugin and factory plugin; one ICON_MISSING warning that the validator says does not change the result)
exit: 0

$ grep -nE "2026-11-17-(71|72|73|74|77|78|79)\b" .sdlc/work/inbox.md; git status --short
(no matches in the inbox; status shows only the two untracked run records)
exit: 0
