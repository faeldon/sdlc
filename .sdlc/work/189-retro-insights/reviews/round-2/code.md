VERDICT: PASS

The change kept last round is done. `test_a_failed_commit_leaves_the_insights_draft_for_a_rerun` in `tests/test_retro.py` makes `git commit` fail with a failing pre-commit hook. It then asserts that:
- `retro-commit` returns 1 and reports `git commit failed`.
- The draft is still on disk, HEAD is unchanged and no report was written.
- After the hook is removed, a rerun returns 0, removes the draft, and the report's Insights section holds the answer.

An implementation that removed the draft before committing would now fail this test.

I did not run it myself. The gate record for round 2, `build/round-2.gate.md`, reads `GATE: PASS`.

## Notes
- The test uses a real hook rather than a stub, so it exercises the actual `git commit` failure path.
- Tests run: none. The gate record covers the suite.
