---
id: 226
slug: scorecard-framework-only
tier: 1
impact: none
stage: shipped
created: 2026-11-22
opened: 2026-11-22T01:11Z
updated: 2026-11-22
shipped: 2026-11-22
idea:
depends_on:
serves: none
---

# 226 — The retro scorecard keeps its framework and drops its build plan

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`docs/RETRO-SCORECARD.md` (602 lines) is two documents. Lines 1–480 are the framework
`/sdlc:retro` reports against: the five pillars, the Value and Trust bands, what each metric means
and where it comes from, the synthesis questions (whose table `tests/test_retro.py:4901` reads),
and Hosts. Lines 481–602, *Seeds to build it* and *Waves* 0–6, are the plan that built it: S1–S17
and R1–R6, with the register ids each wave took in. Waves 0–5 have all landed (160–197), so that
half is history that git already keeps, and a reader has to get past it to the definitions.

The plan's ids leak into the framework too: its 36 `**Status:**` lines say *captured (S12, 168)*,
*needs S7 and S8*, *needs S3*, *needs S16*, ids that now point at nothing, and some of those
"needs" may no longer be true. And `.sdlc/SDLC.md:85` makes this repo's release cadence follow
the waves ("not Release due"), a rule that points at a section about to go.

## Outcome

- `docs/RETRO-SCORECARD.md` ends after *Hosts*: no *Seeds to build it*, no *Waves*, and its
  opening note no longer says the last section lists the seeds.
- Every `**Status:**` line reads *captured* or *not captured: <what is missing>*, checked against
  what `sdlc.py retro` reports today, with no S/R seed id or change number left in it.
- `.sdlc/SDLC.md`'s wave-based release block is gone, so this repo releases on `status`'s
  *Release due*, as the guide says.
- `docs/CONTRIBUTING.md`'s row for the scorecard no longer says "and the seeds that build it".
- `tests/test_retro.py`'s read of the synthesis-questions table, `test_defaults.py` and the
  feature map still pass.

## Affected

- **Area:** contributor docs and this repo's own process doc.
- **Files & components:** `docs/RETRO-SCORECARD.md`, `.sdlc/SDLC.md`, `docs/CONTRIBUTING.md`.
- **Downstream:** no host reads any of them. The plugin reads `.sdlc/SDLC.md` only as this repo's
  answers to the guide, and `test_retro.py` reads the scorecard's questions table.
- **Contracts:** "This repo's process docs hold only its answers" (`test_defaults.py`): deleting
  the block leaves the guide's rule, never a restatement of it.

## Constraints

- The framework's content (each pillar, metric, definition, source and the questions table) stays
  word for word, apart from the Status lines.
- Nothing in the repo may name a host project or a machine path (`test_nothing_local.py`).

## Open questions

- Does this repo want a release rule of its own beside *Release due* (for example, "release before
  each retrospective"), or none?
- Should a metric still marked *not captured* get a seed, or just say so?

## Approach

Delete *Seeds to build it* through the end of `docs/RETRO-SCORECARD.md` and the opening note's
sentence about it. For each `**Status:**` line, check the metric against `sdlc.py retro`'s JSON
and rewrite it as *captured* or *not captured: <what>*, with no seed ids. Delete the release block
at `.sdlc/SDLC.md:85`. Trim the scorecard row in `docs/CONTRIBUTING.md`.

Nits taken in: 2026-11-20-49
