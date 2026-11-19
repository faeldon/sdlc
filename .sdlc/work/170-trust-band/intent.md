---
id: 170
slug: trust-band
tier: 2
impact: minor
stage: shipped
created: 2026-11-19
opened: 2026-11-19T02:20Z
updated: 2026-11-19
shipped: 2026-11-19
idea: 2026-11-18-107
depends_on:
serves: [O4]
---

# 170 — The retrospective says how far its numbers can be trusted

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The scorecard's Trust band (S11) is missing. A retrospective prints its headlines with no sign of
how many changes each rests on, why the rest are missing, or whether something underneath moved
(the Claude Code version, the models, the plugin's own version since the last window), so a thin
number reads as firm as a full one. Idea 2026-11-18-107 adds the host's view: the skills' cases are
this repo's only, so a host's scorecard says nothing of them, and a host with no factory gets the
by-hand view, where mode comparison and pipeline health say "no factory changes" rather than show
zeros.

## Outcome

- Each headline in `retro`'s JSON carries `coverage` (measured of total) and `missing_because`, and
  the report greys a headline under half coverage.
- A *What changed underneath* line compares the Claude Code version, models and plugin version with
  the last window's.
- In a host, cases are never mentioned, and a host with no factory changes says so in place of the
  factory figures. Each is tested on fixtures.
- **Moves O4:** a direction set from the retrospective rests on numbers whose reach is known.

## Affected

- **Area:** the retrospective.
- **Files & components:** `scripts/retro.py`, `scripts/metrics.py` (versions from transcripts or
  trailers), `docs/REFERENCE.md`, tests.
- **Downstream:** every host's retrospective.
- **Contracts:** the metrics trailer format is extended, never redefined; nothing local in a report.

## Constraints

- The report template stays unedited, as with 162.
- No paths in the report.

## Open questions

- ~~Where the Claude Code version comes from at close: the transcripts, or a new trailer.~~
  Resolved: both: read from the transcripts at close, recorded as `Sdlc-Runtime` (spec R1–R3).
