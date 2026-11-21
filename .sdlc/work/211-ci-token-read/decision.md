DECISION: ESCALATE

**Why:** The change is built as specified, and all four reviewers returned PASS. One Outcome clause, "both CI jobs pass on the push that lands it", can't be checked from this repo, because only GitHub Actions on the pushed commit can show it. This run stopped on that untestable requirement, so the only decision allowed is ESCALATE. The diff is small and narrows access without loosening anything.

## Reconsider the approach
Nothing kept coming back across rounds, since there was only round 1 and it was clean. The problem is the Outcome's wording. It joins a claim the repo can check (the `permissions: contents: read` block is present) with one it can't (CI is green on the landing push).

The next step I'd take is to rewrite the Outcome. Keep the grep check in `checks.md` as the testable requirement. Move "both CI jobs pass" out of the Outcome and into a post-landing check: the person looks at the Actions run on the landing commit, or `gh run list` shows it. No code or approach change is needed. Reviewers read every step in both jobs and none writes through `GITHUB_TOKEN`, so the risk is low.

**Open items:** none. Every reviewer passed. These are notes only:
- NIT from the code reviewer: the comment's claim about `setup-uv`'s cache token is not verified against the third-party action. The security reviewer judged the same claim correct.
- PREEXISTING from the security reviewer: actions pinned by tag, not SHA. This is the `notes.md` item below.

**Decisions to confirm:** none. There is no `decisions.md`, and no blocking or open defaults.

**Every other reason for escalating:**
- ESCALATED: look: `.github/workflows/check.yml` — the Outcome's "both jobs pass" can't be tested here. Confirm the Actions run is green on the landing push, or accept it as a post-landing check. The file is `[review] sensitive`.

**For the person at ship:**
- Look first at the 5-line diff in `.github/workflows/check.yml`: the top-level `permissions: contents: read` block after `on:`, and no `permissions:` under either job.
- No published interface is touched.
- The acceptance check in `checks.md` passed when run before and after the edit, and `build/round-1.gate.md` shows `GATE: PASS`.
- After landing, watch the Linux and Windows jobs on the push.

- IMPACT: none — the change only narrows the token CI uses on this repo. No one holding a release receives anything different.

**Undone items:**
- UNDONE: pre-existing: .github/workflows/check.yml:23: `actions/checkout@v4` and `astral-sh/setup-uv@v6` are pinned by moveable tag, not by commit SHA. Pin each to a full SHA with the version in a comment, and let Dependabot or Renovate bump them. → seed: Pin CI actions to commit SHAs

I carried this as a seed rather than a bug. I didn't read the process doc's Bugs section, so I couldn't pick a severity word without guessing.
