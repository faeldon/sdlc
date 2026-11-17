I've resolved the one conflicted file, `.sdlc/work/inbox.md`, with no markers left, and ran no git command. The gate passes on the result: 1956 tests, exit 0.

**From this change:** the deletion of the two bugs it fixes, 2026-11-17-17 (`inbox-commit` calling an entry updated) and 2026-11-17-18 (a reviewer's preamble stopping the run). Ship removes a change's `fixes:` entries like this, and the change's side of the conflict was simply those lines gone.

**From the base branch:** the six entries it filed after those two bugs, kept word for word:
- 2026-11-17-19: port 0 for the factory's UI review server and the board's printed URL.
- 2026-11-17-22: the board's step track reads `decision.md` at any stage.
- 2026-11-17-23 to -26: four board bugs (a card whose file won't read, column order at phone width, the file drawer's missing focus trap, the verifier's chip explained only in a tooltip).

No line in the register still names -17 or -18, so no `After:` reference is left dangling. `sdlc.py check` reports no problems, and I edited no other file.

## Evidence

$ grep -n "2026-11-17-1[78]\b" .sdlc/work/inbox.md
exit: 1

$ uv run --quiet --script scripts/sdlc.py check
■ Problems: 0
    none ✅
exit: 0

$ ./check.sh
All checks passed!
201 files already formatted
1956 passed in 67.78s (0:01:07)
✔ Validation passed
✔ Validation passed
exit: 0
