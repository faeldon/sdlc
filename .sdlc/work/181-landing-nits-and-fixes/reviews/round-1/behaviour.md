VERDICT: PASS

The 12 tests that cover R1 to R8 pass. These are the nit-marker and land-fix tests, plus the skills and prompts checks that name the marker.

## Notes
- The gate record `build/round-1.gate.md` begins `GATE: PASS`. It also shows an earlier attempt that failed, but the final result is a pass.
- `checks.md` does not exist for this change, so there were no acceptance checks to read.
- The spec names no separate end-to-end command, so I ran the tests that exercise the paths it describes:
  - R1 and R2: a nit named in prose stays in the register, and ids on a `Nits taken in:` line in each form are retired.
  - R5 to R8: a fix reported as already made goes on without a commit, a missing or unproven report still stops, and a train goes on to the gate.
  - R4: the skills and README name the `Nits taken in:` marker.
- I did not run the whole suite, since the gate record covers it.

## Evidence
$ head -5 .sdlc/work/181-landing-nits-and-fixes/build/round-1.gate.md
GATE: PASS
(the record has an "Attempt 1 / Verdict: FAIL" section further down)
exit: 0

$ uv run --group dev pytest -q -k "nit_named_but_not or nits_taken_in or fix_already_made or fix_commit_needs_an_ask or asked_at_landing or every_place_that_takes or landings_nits or retires_the_nits or commit_failed_commits or land_fix"
............                                                             [100%]
12 passed, 3180 deselected in 85.18s (0:01:25)
exit: 0
