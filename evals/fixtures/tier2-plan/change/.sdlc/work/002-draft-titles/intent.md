---
id: 002
slug: draft-titles
tier: 2
impact:
stage: plan
created: 2026-11-01
updated: 2026-11-01
idea:
depends_on:
---

# 002 — Rename a saved draft

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

A draft's title is fixed once it is saved: saving the same text under a new title in `drafts.py`
leaves the old title listed beside the new one, so the list fills with duplicates.

## Outcome

- Renaming a saved draft lists it once, under its new title, with its text unchanged.

## Affected

- **Area:** the drafts store.
- **Files & components:** `drafts.py`.
- **Downstream:** `titles()`, which the list reads.
- **Contracts:** none.

## Constraints

- A title is unique: renaming onto a title already saved never loses either draft.

## Open questions

- ~~What happens when the new title is already taken: refuse, or keep both under a suffix?~~
  Resolved: refuse, saying which title is taken.
