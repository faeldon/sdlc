DECISION: READY

**Why:** Round 2 passed from all four reviewers. It reworked the change as the person asked in R1: R4 is now checkable, and the test reads `.yml` and `.yaml` workflows. Every `uses:` in `check.yml` is pinned to a 40-character SHA with a version comment, and the gate is green (3951 passed). The person already acknowledged the sensitive-path look in D1 ("seen"), so nothing else needs their eyes.

**Open items**
- tests/test_ci.py:15: `USES` misses a quoted `uses: "a/b@v4"` (code reviewer, low NIT). An unreadable `uses:` value counts as a failure, so it fails safe.
- tests/test_ci.py:16: `VERSION` demands `v` plus digits (test reviewer, low NIT). This is stricter than the outcome's wording but matches the plan.

**Decisions to confirm:** none. D1 and R1 are both ticked, and there are no open defaults.

**For the person at ship**
- Look first at `.github/workflows/check.yml`, the four `uses:` lines, then at `tests/test_ci.py` and the new `.github/dependabot.yml`.
- The sensitive path and the Dependabot weekly PRs were approved in D1. No published interface is touched.
- After the push, observe CI's run on the pushed commit, which is a post-ship check and not a build requirement.

- IMPACT: none — only CI configuration and a test changed; nobody holding the previous release receives anything different.

**Undone items:** there is no `notes.md`, so there are none.
