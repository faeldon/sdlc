---
id: NNN
slug: SLUG
tier: 1
impact:
stage: plan
created: YYYY-MM-DD
updated: YYYY-MM-DD
idea:
depends_on:
---

# NNN — TITLE

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

<What's wrong or missing today, in the originator's own words. Concrete: name the file, the
component, the screen, or the result someone didn't trust. If this came from an incident or a
surprise, say which one and when.>

## Outcome

<What's true once this is done. Observable, not aspirational: a command someone can run, a test
that passes, a figure that matches.>

## Affected

- **Area:** <which part of the repo: the layer, package or component>
- **Files & components:** <what you expect to touch>
- **Downstream:** <who or what reads what this changes. Something with users is a different risk
  from something with none>
- **Contracts:** <any invariant in the repo's policy doc this comes near, or "none">

## Constraints

<Non-negotiables: what must not break, what must stay true. Only list what actually binds here.>

## Open questions

<Things you don't know yet. It's fine to commit an intent with open questions — that's the point of
Stage 1. Resolve them in the spec or the plan, then close them here in this form:
`- ~~The question?~~ Resolved: what you decided`. The strikethrough is what /sdlc:status counts, so
a question closed in prose alone still reads as open.>

## Approach

<**Tier 1 only** — delete this section for Tier 2, where spec.md and plan.md cover it. A few
sentences on the shape of the fix and which files change. If this section starts wanting
subsections, it's a Tier 2.>
