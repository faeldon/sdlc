---
id: 211
slug: ci-token-read
tier: 1
impact: none
stage: shipped
created: 2026-11-21
opened: 2026-11-21T03:58Z
updated: 2026-11-21
shipped: 2026-11-21
idea: 2026-11-18-74
depends_on:
serves: none
origin: self
---

# 211 — CI's token is read-only

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

From the seed: `.github/workflows/check.yml:13` has no `permissions:` block, so CI runs with the
default `GITHUB_TOKEN`, which can write. A compromised dev dependency running in CI could use a
write-scoped token on this public repo. 152's review found it and left it undone as pre-existing.

## Outcome

`check.yml` declares `permissions: contents: read` at the top level, and both CI jobs (Linux and
Windows) still pass on the push that lands it. A grep in `checks.md` confirms the block is there.

## Affected

- **Area:** CI.
- **Files & components:** `.github/workflows/check.yml` only.
- **Downstream:** CI runs on this repo, which need only read access to check out the code.
- **Contracts:** `.github/workflows/` is `[review] sensitive`, so it gets the full review.

## Constraints

- No job loses a permission it uses: today the workflow checks out, runs `./check.sh` and the
  portable tests, and uploads nothing.

## Open questions

- Does any step need more than `contents: read` (an artifact upload, a cache write)? The plan
  confirms it from the workflow.

## Approach

Add a top-level `permissions:` block with `contents: read` to `check.yml`, after `on:`, and confirm
both jobs pass. One file.

Nits taken in: none
