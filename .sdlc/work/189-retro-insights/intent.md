---
id: 189
slug: retro-insights
tier: 2
impact: minor
stage: shipped
created: 2026-11-20
opened: 2026-11-19T23:48Z
updated: 2026-11-20
shipped: 2026-11-20
idea: [2026-11-20-5, 2026-11-19-63, 2026-11-19-64]
depends_on:
serves: [O4]
---

# 189 — The retrospective's report answers its own questions: the Insights section

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Since 184, the retrospective opens with the scorecard, but it stops at figures: the synthesis, what
the figures mean together and what to do about them, is still left to the person reading. S15
(2026-11-20-5): "The Insights section: the synthesis questions in a guide file a host can extend,
each answered by a read-only sub-agent on its pillar's data, in the fixed answer shape."

`render_report()` has also grown to eight positional blocks and five keyword ones, and 184 left two
follow-ups: 2026-11-19-63, pass `report_figures()`'s dict whole; and 2026-11-19-64, scorecard rows
say `none in the window` for response, autonomy and workarounds even when the window held changes
that just weren't measured, because those blocks carry no `missing_because`. Two nits sit on the
same code: 2026-11-19-65 (`_trend` compares an unrounded value with a rounded `last`, so 0.174
against a written 0.17 reads `up`) and 2026-11-19-66 (`_minutes` rounds small medians to whole
minutes).

## Outcome

- The report has an `## Insights` section: each pillar's synthesis question, from a guide file a
  host can extend, answered by a read-only sub-agent on that pillar's figures alone, in one fixed
  answer shape.
- `render_report()` takes the figures as one dict.
- Every null scorecard row names its real reason.
- The nits are fixed or answered.
- **Moves O4:** the person reads what the figures mean, with the evidence cited, rather than
  working it out from the tables.

## Affected

- `scripts/retro.py`, `skills/retro/SKILL.md`, a new guide file under `guide/`,
  `templates/retro.md` (irreversible), `agents/`, `docs/REFERENCE.md`, `tests/test_retro.py`.
- **What reads it:** every host's retrospective; the template override contract (`TEMPLATE_READS`)
  and `drift`.

## Constraints

- `retro` stays read-only but for its report.
- Every core agent has Read, Grep and Glob and nothing that writes.
- A host's override without the new placeholder still renders.
- The guide file's shape follows `tests/test_defaults.py`.

## Open questions

- ~~Does each pillar's sub-agent run inside the skill, or through a script command?~~ Resolved:
  inside the skill, through `Agent` (`sdlc:insight`); the script cuts the figures (spec R3, R9).
- ~~Is the answer shape fixed by the guide or by the script?~~ Resolved: by the script (spec R5).
- ~~What does a host's extension of the guide look like?~~ Resolved: `.sdlc/INSIGHTS.md`, read
  block by block after the guide (spec R2).
