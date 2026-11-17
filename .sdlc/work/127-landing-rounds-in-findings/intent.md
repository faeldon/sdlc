---
id: 127
slug: landing-rounds-in-findings
tier: 1
impact: patch
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: 2026-11-18-7
depends_on:
serves: [O6]
---

# 127 — A landing's review rounds go into findings.md

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Since 114, `factory.py carry` writes every complete build round's agent findings into
`findings.md` (`agent_findings()`, `write_findings()`), but the landing's review rounds
(`reviews/land-<n>/`) are left out: 114's notes, "`findings.md` holds only the build rounds
(`reviews/round-<N>/`); the landing's review rounds (`reviews/land-<n>/`) are not in it." A CHANGE
a landing reviewer raised and the builder fixed, as 110's and 116's landings had, never reaches
the record retro compares, so the factory's review looks lighter than it was.

## Outcome

- The landing writes its rounds' findings into `findings.md`, each `Class:` naming its landing
  round, in `carry`'s section shape and rules, before `land --close` commits.
- A rerun still rewrites only the agents' sections, and a landing commit still has no
  `Sdlc-Findings`.
- A test builds a landing round with a kept, a dropped and a pre-existing line and finds each once.
- **Moves O6:** retro counts what a landing review caught.

## Affected

- **Area:** the factory's landing and its findings record.
- **Files & components:** `plugins/factory/scripts/factory.py` (`write_findings()`,
  `agent_findings()`, the landing's close path); `tests/test_land.py`.
- **Downstream:** retro's `review_sources`.
- **Contracts:** a factory review is never counted as the person's; `findings.md` keeps one shape.

## Constraints

- The agents' findings stay apart from ship's (`ship_findings()`).

## Open questions

- Which landing step writes it: `land-verdicts` at `pass`, or `land --close`?
- Is a finding a reviewer raised in both a build round and a landing round one or two?

## Approach

Let `agent_findings()` take the landing rounds the landing already reads, and call
`write_findings()` from the landing before its record joins the commit.
