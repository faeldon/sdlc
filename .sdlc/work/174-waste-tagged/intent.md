---
id: 174
slug: waste-tagged
tier: 2
impact: minor
stage: shipped
created: 2026-11-19
opened: 2026-11-19T07:56Z
updated: 2026-11-19
shipped: 2026-11-19
idea: 2026-11-19-31
depends_on:
serves: [O4, O5]
---

# 174 — The retrospective says what a change cost, and what was wasted

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The scorecard's Cost pillar (`docs/RETRO-SCORECARD.md`, S4) has no figure across changes. Each
factory change's dollars, tokens and duration are in its `runs/costs.jsonl`, summed for one change
only by `factory.py ready`, and `retro` reports none of them. A row says what a run cost but not
what it was for, so the spend that bought nothing (an ejected change, a red gate's fix, a rework
round, a rerun, a mend) can't be told from the build itself. Idea 2026-11-19-31: "each agent run
marked by what it was for (build, rework, red-gate fix, ejected, rerun, mend), and retro reports
the waste share and cost per landed change."

Two nits on `scripts/metrics.py` come in: 2026-11-19-16 (the `bg` regex counts an unquoted `&`
inside a URL such as `curl x?a=1&b=2`, which is correct shell, but no test pins the choice) and
2026-11-19-22 (`runtime_trailer()` puts no limit on a version or model value, so an odd transcript
value makes a very long trailer line; cap each, e.g. at 64 characters).

## Outcome

- Each row `factory.py` writes to `runs/costs.jsonl` says what the run was for, from a fixed set
  of purposes; a run whose work was later thrown away (its change ejected or dropped) counts as
  waste without its row being rewritten.
- `retro`'s JSON gains the Cost pillar's figures, each with its `n`: dollars and agent-minutes per
  landed change by tier, the waste share and its parts, and spend by role and model, read only
  through `scripts/factory_records.py`, with a test on fixture runs.
- The two nits are fixed or answered.
- **Moves O4:** the retrospective says what a change costs and where money went on work that
  didn't land.
- **Moves O5:** what the factory costs a host per change is a number it can watch, not a guess.

## Affected

- **Area:** the factory's run records, metrics and the retrospective.
- **Files & components:** `plugins/factory/scripts/factory.py` (where `COSTS` rows are written),
  `scripts/factory_records.py`, `scripts/retro.py`, `scripts/metrics.py`, `docs/REFERENCE.md`
  (*Retrospectives*), the Cost rows of `docs/RETRO-SCORECARD.md`.
- **Downstream:** every factory run writes the new field; the board reads `costs.jsonl` for a
  run's step seconds (`board.py`), so the row must stay readable by it; a host's retrospective.
- **Contracts:** core reads a run's records only through `factory_records.py`, under
  `factory.py`'s names, its copies pinned by `tests/test_modules.py`; metrics' trailers are
  extended, never redefined; `retro` writes nothing but its report.

## Constraints

- A row written before this change, with no purpose, still reads: counted in cost, never as
  waste, and the trust band says how many.
- A hand-built change records tokens, not dollars: its cost is reported as missing, never as $0.

## Open questions

- ~~Is the purpose written when the run starts (`agent --task` knows it), or derived by `retro`
  from the run's task and what later happened to its change?~~ Resolved: both; the run writes its
  purpose, `retro` derives ejected and dropped (spec R1–R6).
- ~~Does a mend count as waste, or as the price of a readable reply?~~ Resolved: waste, reported as its
  own part (spec R6).
- ~~When an ejected change lands later, is its first landing's spend waste?~~ Resolved: only the
  ejected attempt's landing runs (spec R6).
