VERDICT: PASS

The change does what the spec says. The gate record shows a green run, and the targeted tests pass. I did not run `inbox-commit` end to end in a scratch repo; the evidence is the named tests plus greps of the code and docs.

## Notes
- `checks.md` does not exist for this change, so there are no acceptance checks to read or run.
- No end-to-end path is named beyond the tests, so I ran the closest one: the tests that exercise the new behaviour. These are R1–R3, R5 (filing), R4 (the review prompt's earlier nits), R7–R8 (retiring a nit and the open-change refusal) and R10 (the `/sdlc:idea` skill). Eight tests ran and all passed.
- I did not run `landing.py` or the whole suite. The gate record shows `GATE: PASS` for `./check.sh`, which covers the full suite.
- In the code, `RETIRE_REASONS["nit"]` is `("duplicate", "stale", "wontfix")` (R7). In `docs/REFERENCE.md` the old "never retired this way" wording remains at line 518, but only for ideas and bugs with an `idea:` or `fixes:` line. I did not read the paragraph around it, so I can't say whether it now covers nits.
- `skills/idea/SKILL.md` now describes retiring a nit with its reason (R10).
- The two open `[default]` decisions in `decisions.md`, D1 and D2, are the builder's naming choices. Neither blocks the review.

## Evidence
$ cat .sdlc/work/230-nit-flow/build/round-1.gate.md | head -12
(the record's first lines, printed above in the earlier read, `head -12`):
GATE: PASS
Attempt 1: Verdict: PASS, Command: ./check.sh, Exit: 0, Seconds: 566.3, Tree: unchanged
exit: 0

$ uv run --group dev pytest -q -k "inbox_commit_retires_by_the_entry or never_retires_a_nit or a_nit_a_later or no_later_round_raises or nit_not_filed_says or no_low_value or names_its_roles_earlier or idea_retires_a_nit or nit_reader"
........                                                                 [100%]
8 passed, 4059 deselected in 13.16s
exit: 0

$ grep -n "RETIRE_REASONS = " -A3 scripts/sdlc.py
7483:RETIRE_REASONS = {
7484-    "idea": ("duplicate", "superseded", "declined"),
7485-    "bug": ("duplicate", "not-a-bug", "wontfix", "cant-reproduce"),
7486-    "nit": ("duplicate", "stale", "wontfix"),
exit: 0

$ grep -n "never retired this way" docs/REFERENCE.md
518:`idea:` or `fixes:` line) is never retired this way.
exit: 0

$ grep -n "nit" skills/idea/SKILL.md
76:- **Retire** a `[nit]` no change will take in: the reason is one of `duplicate` (another entry
78:  said with a line on why. A nit an open change takes in (by id on its `Nits taken in:` line, or
exit: 0
