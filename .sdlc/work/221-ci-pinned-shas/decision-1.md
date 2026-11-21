DECISION: ESCALATE

**Why:** The build matches the plan and all four reviewers passed it. Both pinned SHAs were checked against upstream with `git ls-remote`, and the gate is green. The run stops here because the builder reports R4 ("CI is green on the change's commit") can't be tested before a push. The skill refuses any other decision for that. The edit is also to `.github/workflows/`, a `[review] sensitive` path.

**Open items**
- tests/test_ci.py:52: the glob reads only `*.yml`, so a `.yaml` workflow, which GitHub also runs, would go unchecked (security reviewer, med). Not blocking, but cheap to fix before landing.
- tests/test_ci.py:15: `USES` misses a quoted `uses: "a/b@v4"` (code reviewer, low). The security reviewer notes that anything unreadable as a pin counts as a failure, so this may already fail safe.
- tests/test_ci.py:16: `VERSION` demands `v` plus digits, which is stricter than the outcome's wording but matches the plan (test reviewer, low).

**Decisions to confirm:** none. There is no `decisions.md`, so no blocking decision or open default exists.

**Other reasons to escalate**
- ESCALATED: look: `.github/workflows/check.yml` and `.github/dependabot.yml` — the change touches a sensitive path. Check that the two pins, `11d5960a…` (checkout v4.4.0) and `d0cc045d…` (setup-uv v6.8.0), are what you want CI to run. Confirm Dependabot's weekly PRs are wanted. R4 can only be seen on the pushed commit's CI run.

## Reconsider the approach
This round didn't fail to converge. The one blocker is that R4 can't be tested inside the build, because it needs a push and a GitHub runner. The next step is to rewrite R4. Replace "CI is green on the change's commit" with checkable outcomes: both `uses:` lines are SHA-pinned, `tests/test_ci.py` passes, and the gate is green. Treat the CI run on the pushed commit as a post-ship observation, not a build requirement. R1–R3 are covered by the tests and the acceptance check. Nothing else in the approach needs to change. Optionally, ask the builder for one small follow-up that globs `*.yaml` as well.

**For the person at ship**
- Look first at `.github/workflows/check.yml`, the four `uses:` lines and the comment above `permissions:`.
- Then look at `tests/test_ci.py`'s `USES` and glob, and at the new `.github/dependabot.yml`.
- No published interface is touched.
- After the push, confirm CI is green.

- IMPACT: none — only CI configuration changed; nobody holding the previous release receives anything different.

**Undone items:** `notes.md` doesn't exist, so there are none.
