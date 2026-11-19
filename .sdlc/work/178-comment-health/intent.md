---
id: 178
slug: comment-health
tier: 2
impact: none
stage: shipped
created: 2026-11-19
opened: 2026-11-19T07:57Z
updated: 2026-11-19
shipped: 2026-11-19
idea: 2026-11-19-9
depends_on: [177]
serves: [O4, O5]
---

# 178 — Comment health as an indicator

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Idea 2026-11-19-9, in its own words: "Agent-written code tends to over-comment (RealHumanEval:
about 2x the comments; it narrates when unsure), while too few comments make complex code
unauditable, and comment text is roughly 30% of what agents read in this repo's scripts. No
research gives one right ratio (open-source norm about 19% of lines, Arafat & Riehle 2009), so
measure four signals rather than one: per-file density as a band (flag <0.10 or >0.40) and its
trend across the window; docstring coverage of long (>=30 lines) and hot functions; the share of
narration comments that restate their line; and the comment share of agent input tokens. Ship it
as an indicator script beside .sdlc/function-heat.py (this repo's, Python), reported through
retro.indicators in the Quality pillar with Cost as its guardrail."

It follows indicators-structured, whose row shape it prints.

## Outcome

- `.sdlc/comment-health.py`, set in this repo's `retro.indicators`, prints the four signals as
  indicator rows, and the retrospective shows them in the Quality pillar.
- It writes nothing and names functions and numbers only, as `function-heat.py` does.
- **Moves O4:** the retrospective shows whether agent-written code is drifting towards narration
  or towards silence.
- **Moves O5:** comments' share of what agents read is a number, so trimming them can be weighed.

## Affected

- **Area:** this repo's indicators.
- **Files & components:** `.sdlc/comment-health.py` (new), `.sdlc/config.toml`,
  `docs/RETRO-SCORECARD.md` (S17's row), its tests.
- **Downstream:** this repo's retrospective; no host, since the script is this repo's own.
- **Contracts:** the indicator row shape indicators-structured sets.

## Constraints

- Python only, like `function-heat.py`: it measures this repo, not a host's languages.
- Read-only, and quick enough for the evidence timeout.

## Open questions

- ~~How is a narration comment told from a useful one without a model call?~~ Resolved: word
  overlap with the line it describes, read with `tokenize` (spec R7).
- ~~Where does "the comment share of agent input tokens" come from: the files agents `Read`, from
  the transcripts, or an estimate from the files themselves?~~ Resolved: an estimate from the files
  (spec R8).
