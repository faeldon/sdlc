---
id: 175
slug: pipeline-figures
tier: 2
impact: minor
stage: shipped
created: 2026-11-19
opened: 2026-11-19T07:57Z
updated: 2026-11-19
shipped: 2026-11-19
idea: 2026-11-19-34
depends_on: [174]
serves: [O4]
---

# 175 — The retrospective reports the pipeline's gates, trains and reviews

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The scorecard's Speed diagnostics and Quality risk figures (S10) are recorded in every factory
change's folder and read by nothing across changes: the gate's seconds and attempts in
`build/*.gate.md` and `build/land-*.gate.md`, the train's steps in `runs/land-train.md` and
`runs/land-times.jsonl`, the mends in `runs/mended`, the depth each round ran at, and the
`unreviewed=` count on `Sdlc-Landed`. Idea 2026-11-19-34: "gate seconds and slot-wait trend,
red-gate rate, train figures (gates, ejections, bisections, base moves, accept stops, conflicts),
mends, full-depth share, unreviewed landings." Today's comparison of trains against one-at-a-time
landing had to be counted by a script outside the plugin.

Two nits on the same readers come in: 2026-11-19-19 (`autonomy_counts` checks the `SUPERSEDED`
and `SETTLED` marks under `defaults` only; a one-line comment would say why blocking and look
lines need none) and 2026-11-19-21 (`_none_reason()`'s `(\s+\S+=\S*)+$` backtracks badly on a
hand-written `Sdlc-Coverage` with many `a=b=c` tokens; use `(\s+[^\s=]+=\S*)+$`).

It follows waste-tagged, which adds to the same reader and the same part of `retro`'s JSON.

## Outcome

- `retro`'s JSON gains the pipeline's figures, each with its `n`: the gate's median and 85th
  percentile seconds and its slot wait, by window; the red-gate rate per build; per landed change,
  the landing gates, ejections by cause, bisections, base moves, accept stops and conflicts
  resolved; mends per change; the share of runs at full depth; and the landings with paths no
  review read. All read through `scripts/factory_records.py`, with a test on fixture runs.
- The two nits are fixed or answered.
- **Moves O4:** the retrospective shows where the pipeline spends time and where it takes risks,
  so a change to the landing or the gate can be judged by its numbers.

## Affected

- **Area:** the factory's run records and the retrospective.
- **Files & components:** `scripts/factory_records.py`, `scripts/retro.py`, `docs/REFERENCE.md`
  (*Retrospectives*), the Speed and Quality rows of `docs/RETRO-SCORECARD.md`.
- **Downstream:** a host's retrospective; anyone comparing landing strategies.
- **Contracts:** core reads a run's records only through `factory_records.py`, its copies of
  `factory.py`'s parsing pinned by tests; `retro` is read-only but for its report.

## Constraints

- No new trailer unless a figure exists only while the change lands; a new one extends metrics'
  contract, never redefines it.
- A figure a record doesn't hold for an older change is missing, counted in the trust band, never
  zero.

## Open questions

- ~~Are the train's figures read from the change's records at its `Close` commit's parent, or
  written as a trailer when it closes?~~ Resolved: read from the records at the change's own
  commit (spec R5).
- ~~Do the gate files record the slot wait today, or does it need adding first?~~ Resolved: it
  doesn't; both gate writers gain a `Waited:` line (spec R3).
