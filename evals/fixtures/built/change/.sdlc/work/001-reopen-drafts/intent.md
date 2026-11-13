---
id: 001
slug: reopen-drafts
tier: 1
impact:
stage: build
created: 2026-11-01
updated: 2026-11-01
idea:
depends_on:
---

# 001 — Reopen a saved draft

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`drafts.py` can save a draft and list the saved titles, but nothing gives a saved draft's text
back, so a draft can't be reopened to keep writing it.

## Outcome

- `drafts.reopen(title)` returns the saved text, and `None` for a title never saved.

## Affected

- **Area:** the drafts store.
- **Files & components:** `drafts.py`.
- **Downstream:** nothing else reads it yet.
- **Contracts:** none.

## Constraints

- Saving and listing behave as before.

## Open questions

- ~~Should reopening an unknown title raise?~~ Resolved: it returns `None`.

## Approach

Add `reopen()` beside `save()`, reading the same dictionary.
