VERDICT: CHANGES

- CHANGE: tests/test_retro.py: R6 says a failed `git` step leaves the draft on disk so a rerun finds it, and no test covers it. `test_retro_commit_renders_the_insights_and_removes_the_draft` only covers the success path. A change that unlinked the draft before the commit would pass every test. Add a test that makes the commit step fail (for example, a stub `sdlc._git` that raises or returns nonzero on `commit`), then asserts `retro-commit` fails, the draft still exists, and a rerun after the fix commits it and removes it.

## Notes

- **Gate.** `build/round-1.gate.md` is `GATE: PASS` from `./check.sh`, with `3463 passed, 29 skipped`. I ran nothing myself.
- **Requirement-to-test map.** Every R1–R14 test the spec or plan names exists. I read the bodies of R2, R3, R6 and R7 (`test_a_host_insights_doc_replaces_adds_and_places`, `test_each_insight_gets_only_its_pillars_figures`, `test_retro_commit_renders_the_insights_and_removes_the_draft`, `test_the_insights_say_not_answered_without_a_draft`) and the R8 override test. They assert specifics and can fail.
- **Well covered.** R2's four rules plus the duplicate title are in one test. R6's success case checks the draft is out of `paths`, out of the commit's file list and off disk, and that the tree is clean. R7 also checks that `retro --report` writes nothing.
- **Not read.** I did not open the R4 marker-file test, `test_retro_commit_refuses_a_seed_the_register_lacks`, the R9 skill test or the R5 agent test.
- **Checks.** There is no `checks.md`, and none is needed.
- NIT: tests/test_retro.py:4867: the `test_config_reports_the_insights_doc` "off while it doesn't exist" assertion only checks that no warning mentions INSIGHTS, so it is weak {tests S low}
