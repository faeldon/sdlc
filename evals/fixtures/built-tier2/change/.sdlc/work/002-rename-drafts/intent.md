---
id: 002
slug: rename-drafts
tier: 2
impact:
stage: build
created: 2026-11-01
updated: 2026-11-01
idea:
depends_on:
---

# 002 — Rename a saved draft

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

A draft saved under the wrong title stays under it: `drafts.py` can save and list drafts, but
nothing moves one to a new title.

## Outcome

- `drafts.rename(old, new)` moves a saved draft's text to the new title.

## Affected

- **Area:** the drafts store.
- **Files & components:** `drafts.py`.
- **Downstream:** nothing else reads it yet.
- **Contracts:** none.

## Constraints

- Saving and listing behave as before.

## Open questions

- ~~What happens on a taken title?~~ Resolved: nothing changes, and `rename` returns `False`.
