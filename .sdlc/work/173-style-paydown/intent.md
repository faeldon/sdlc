---
id: 173
slug: style-paydown
tier: 1
impact: none
stage: shipped
created: 2026-11-19
opened: 2026-11-19T02:21Z
updated: 2026-11-19
shipped: 2026-11-19
idea: [2026-11-18-89, 2026-11-18-81, 2026-11-18-82]
depends_on:
serves: none
---

# 173 — Pay down the style nits in one change

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The register holds a dozen line-width and doc nits, each too small for a change of its own, on
files wave 2's other changes also edit, so this lands last. Ideas 2026-11-18-89 (this pay-down),
-81 (the reviewer agents' lines past 100 columns) and -82 (the factory README's); nits -75, -77,
-78 (`check.yml`'s header comment), -83 and 2026-11-19-5 (long AGENTS.md lines), -96 (a factory
README bullet), 2026-11-19-10 (another README line), -76 (the skip-note question in `check.sh`'s
summary) and -108 (`heat()`'s blame edge undocumented).

## Outcome

- Every line those entries name wraps near 100 columns, as its file does.
- -76 is answered in `check.sh`'s summary or its doc, and -108 gets its one-line comment.
- No behaviour changes; the gate is green.

## Affected

- **Area:** docs, comments and agent files.
- **Files & components:** `.github/workflows/check.yml`, `AGENTS.md`, `plugins/factory/README.md`,
  `plugins/factory/agents/*.md`, `.sdlc/function-heat.py`, `check.sh` or its doc.
- **Downstream:** people only; CI runs `check.yml`, which a comment change doesn't affect.
- **Contracts:** none.

## Constraints

- Rewrap only, but for -76 and -108.
- `check.yml` is `[review] sensitive`, so the run is reviewed at full depth.

## Open questions

None.

## Approach

Rewrap each named line, answer -76 with a sentence, and add -108's comment. Land it after the other
wave 2 changes, so their edits to the same files are in. Nits taken in: 2026-11-18-75,
2026-11-18-77, 2026-11-18-78, 2026-11-18-83, 2026-11-18-96, 2026-11-19-5, 2026-11-19-10,
2026-11-18-76, 2026-11-18-108.
