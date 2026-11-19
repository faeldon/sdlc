VERDICT: PASS

## Notes

Every requirement from R1 to R14 maps to a test that would fail without the change. R15 (the docs) has no test, as the plan says. I judged the R1 to R5 tests by reading them. For R6 to R14 I relied on the gate's pass and the test names and docstrings, so those tests were not read.

- **R1:** `test_close_names_each_skill_it_ran` types a skill twice and calls another through the Skill tool. It asserts the run counts, the trailer lines and the read-back. It also checks that a commit with no `Sdlc-Skill` line has no `skills` key, so it reads as unrecorded and never as zero.
- **R2, R3:** The surface test adds a made-up skill, command and config key to a copy of the code, so it fails if any list is kept by hand. The factory regex is pinned to both scripts' own `COMMANDS`. The factory's items appear only when it is enabled or the repo is the plugin's own.
- **R4, R5:** `test_a_call_counts_once` puts the same calls on both `Sdlc-Tool` and `Sdlc-Calls` and checks they are counted once. The unmeasured test checks all three reasons, and that nothing marked `unused` carries a `why`.
- **R8 to R10:** There are tests for the retire rule (needs N windows, an unmeasured window breaks the run, too few windows names nothing), the footprint and the growth rows.
- **R11 to R14:** The feature-map tests read the code for stages, tiers, impacts, nit costs and values, review passes, skills, board columns and trailers, and compare them with the entries. They also check `Specified:` paths, `Depends on:` terms, the graph nodes against the `##` sections, the `WAIT:` nodes against the skills that have a WAIT heading, and that neither map cites a change by folder number or holds HTML.
- **The gate:** Its record is `build/round-1.gate.md`. It shows `3178 passed, 29 skipped in 157.36s`, and plugin validation passed. I did not run the suite or any other test.
- **checks.md:** The change has no `checks.md`, so there were no acceptance checks to review.

- NIT: tests/test_metrics.py:495: the docstring starts "179 R1", which cites the change by number; the rest of the repo's test docstrings name only the behaviour {style S low}
