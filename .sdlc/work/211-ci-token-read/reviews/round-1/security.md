VERDICT: PASS

## Notes

The change adds a top-level `permissions:` block with `contents: read` to `.github/workflows/check.yml`, with a comment saying why. Nothing else in the workflow changed.

**Trust boundary.** The risk is third-party code that runs in CI: `actions/checkout`, `astral-sh/setup-uv`, the PyPI dev dependencies `uv` installs, and Playwright's Chromium download. Before this change all of it ran with the default `GITHUB_TOKEN`, which could write. Checked with STRIDE:
- **Tampering and elevation of privilege:** a compromised dependency could have pushed to a branch, rewritten a tag or edited a release. With `contents: read` and every other scope at `none`, it can't. This is what the change fixes, and it fixes it.
- **Information disclosure:** the token can still read contents, but the repo is public, so that exposes nothing new.
- **Denial of service:** no new jobs or triggers.

**Nothing breaks.** I read each step in both jobs:
- `checkout` needs only `contents: read`.
- The `git config` lines and the `ruff`, `pytest` and `playwright install` steps don't use the token.
- `setup-uv@v6` reads its release from GitHub, which needs no write scope on a public repo. Its cache, if it runs, goes through the runner's own cache token (`ACTIONS_RUNTIME_TOKEN`), not `GITHUB_TOKEN`. The comment in the diff says this correctly.
- No step uploads, comments or pushes.
- Neither job sets its own `permissions:`, so neither widens the top-level block.

The intent's open question (does any step need more than `contents: read`?) is answered: no.

**Acceptance check.** The `checks.md` grep fails if the block is missing, if the line after it isn't `  contents: read`, or if a second scope sits under it. It also fails if `permissions:` appears more than once, which would catch a job widening it. The new comment doesn't contain the string `permissions:`, so the count of exactly one holds.

**Gate.** `build/round-1.gate.md` shows `./check.sh` passed (exit 0, tree unchanged). I didn't rerun it.

**Medium, already in the repo before this change:** both jobs pin actions by tag (`@v4`, `@v6`), not by commit SHA. Whoever controls a tag could move it to other code, which would still run with read-only access and the runner's cache token. Now that the token is read-only, the damage is limited to CI's own results and the cache.
- PREEXISTING: .github/workflows/check.yml:23: `actions/checkout@v4` and `astral-sh/setup-uv@v6` are pinned by moveable tag, not by commit SHA. Pin each to a full SHA with the version in a comment, and let Dependabot or Renovate bump them.

**What's done well:** the scope is the smallest that works, it is set once at the top level so a new job gets it too, and the comment says why each step needs no more.

**What I read:** `intent.md`, `checks.md`, the diff, the whole workflow file and the gate record. There was no `decisions.md`.
