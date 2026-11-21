# 211-ci-token-read — entries

## [2026-11-21-22] [idea] Pin CI actions to commit SHAs

Left undone by 211-ci-token-read, carried forward when it landed: pre-existing: .github/workflows/check.yml:23: `actions/checkout@v4` and `astral-sh/setup-uv@v6` are pinned by moveable tag, not by commit SHA. Pin each to a full SHA with the version in a comment, and let Dependabot or Renovate bump them.
See .sdlc/work/211-ci-token-read/notes.md in its commit.
Raised 2026-11-21.

## [2026-11-21-23] [nit] the comment's claim that setup-uv's cache uses the runner's own cache token is an unverified claim about a third-party action.

Raised by the code review of 211-ci-token-read, round 1: .github/workflows/check.yml:14: the comment's claim that setup-uv's cache uses the runner's own cache token is an unverified claim about a third-party action. The rest of the comment is checkable from the file.

Theme: docs
Paths: .github/workflows/check.yml
Cost: S
Value: low
Raised by: 211-ci-token-read (correctness)
