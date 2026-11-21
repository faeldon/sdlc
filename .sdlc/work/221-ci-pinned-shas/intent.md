---
id: 221
slug: ci-pinned-shas
tier: 1
impact: none
stage: shipped
created: 2026-11-21
opened: 2026-11-21T14:25Z
updated: 2026-11-22
shipped: 2026-11-22
idea: 2026-11-21-22
depends_on:
serves: none
origin: self
---

# 221 — CI's actions are pinned to commit SHAs

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

From seed 2026-11-21-22, left by 211-ci-token-read's security review: `.github/workflows/check.yml`
uses `actions/checkout@v4` and `astral-sh/setup-uv@v6`, pinned by moveable tag, not by commit SHA.
A tag can be moved to other code, which then runs in this repo's CI with its token.

## Outcome

- Every `uses:` in `.github/workflows/` names a full 40-character commit SHA, with the version it
  is in a trailing comment (`# v4.2.2`).
- A test fails on a `uses:` pinned by tag or branch.
- Dependabot (`.github/dependabot.yml`, `github-actions` ecosystem) proposes bumps, so the pins
  don't rot.
- Both of `check.yml`'s actions are SHA-pinned, `tests/test_ci.py` passes (reading `.yml` and
  `.yaml` workflows alike, since GitHub runs both), and the gate is green. CI's run on the pushed
  commit is observed after ship, not a requirement of the build.

## Affected

- **Area:** CI.
- **Files & components:** `.github/workflows/check.yml`, a new `.github/dependabot.yml`, a test in
  `tests/`.
- **Downstream:** CI on every push; no host reads it.
- **Contracts:** `[review] sensitive` names `.github/workflows/`, so the full review runs.

## Constraints

- The pinned SHAs are the commits the current tags point at, so CI's behaviour doesn't change.

## Open questions

- Dependabot, or a test that only refuses tags, with bumps by hand?

## Approach

Resolve each action's current tag to its commit (`gh api repos/<owner>/<repo>/git/ref/tags/<tag>`),
write the SHA with the version comment, add `dependabot.yml` for `github-actions`, and a test that
reads the workflows and refuses any `uses:` not pinned to a 40-hex SHA.
