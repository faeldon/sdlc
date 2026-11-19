---
id: 177
slug: indicators-structured
tier: 2
impact: minor
stage: shipped
created: 2026-11-19
opened: 2026-11-19T07:57Z
updated: 2026-11-19
shipped: 2026-11-19
idea: 2026-11-19-32
depends_on:
serves: [O4]
---

# 177 — The retrospective reads indicators as rows and shows them as a table

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

A host's `retro.indicators` are commands whose output `retro` passes through unread, as `host`
(`_evidence()` in `scripts/retro.py`): this repo's own, `.sdlc/function-heat.py`, prints ranked
lines a reader has to parse by eye, and the report can't compare a figure with the last
retrospective's. The scorecard's Quality pillar (S8) needs them as data. Idea 2026-11-19-32:
"retro.indicators emit JSON rows, rendered as a table in the report; 'no indicators set' said when
empty; setup offers the key." Comment health (2026-11-19-9) waits on it.

## Outcome

- An indicator command may print JSON rows in a documented shape; `retro` reads them, and the
  report renders them as a table, each figure against the last retrospective's where both exist.
- Output that isn't in that shape still passes through as today, so no host's indicator breaks.
- The report says "no indicators set" when the key is empty.
- `/sdlc:setup` offers the key.
- `.sdlc/function-heat.py` prints the new shape.
- **Moves O4:** a host's own structural figures sit in the retrospective as numbers with a trend,
  not as text.

## Affected

- **Area:** the retrospective and setup.
- **Files & components:** `scripts/retro.py`, the retrospective's report template, `skills/setup/`,
  `guide/` or `defaults/` where the key is offered, `.sdlc/function-heat.py`, `docs/REFERENCE.md`
  (*Retrospectives*, *After an update*).
- **Downstream:** every host with `retro.indicators` set; setup's question on an update.
- **Contracts:** the indicator row shape becomes a contract hosts write to; setup's `drift()` and
  `readiness` if `defaults/` changes (`sdlc.py record` in the same change).

## Constraints

- Plain-text output keeps working.
- An indicator still runs as `retro.evidence` does, under its timeout and limit, and a failure is
  a row, never a failed retrospective.

## Open questions

- ~~What is the row shape: name, value, unit and band, or something a host can extend?~~ Resolved: JSON Lines with `name`, numeric `value` and optional `unit`, other keys kept as `extra`; no band (spec R1).
- ~~Does setup offer the key on every update, or only when it isn't set?~~ Resolved: only when `retro.indicators` is empty, in setup's drafts step (spec R11).
