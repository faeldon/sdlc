---
id: 168
slug: work-mix-and-follow-through
tier: 2
impact: minor
stage: shipped
created: 2026-11-19
opened: 2026-11-19T02:20Z
updated: 2026-11-19
shipped: 2026-11-19
idea:
depends_on:
serves: [O4]
---

# 168 — The retrospective reports work mix, follow-through and time to users

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The scorecard (`docs/RETRO-SCORECARD.md`) names three Value-band numbers `sdlc.py retro` doesn't
compute: work mix (S2: each landed change classed capability, fix, debt or process from its
`impact:`, its seed's tag, `fixes:`, `reworks:` and theme, with the shares reported),
follow-through (S12: the share of the last retrospective's seeds, milestones and intents done or
dropped against carried or vanished) and time to users (S13: the median time from landing to
release, and releases per window). Without them the retrospective can say how fast changes land but
not whether they were the right work, whether last time's plans were kept, or how long users wait.
Three nits on `scripts/metrics.py` sit on the same path: 2026-11-18-64 (`bg` only looks for a
trailing `&` at the end of the whole command), -65 (the `uvx`/`npx` program-list slice is only right
when the program is the first non-flag word) and -97 (`FACTORY_CHECK_RE` accepts a quote after
`.py`).

## Outcome

- `sdlc.py retro`'s JSON gains `work_mix`, `follow_through` and `time_to_users`, each with its `n`
  and an `unmeasured` count, never a zero for missing data, and the report shows them in the Value
  band. A test fails for each on a fixture history: a known mix, a retrospective whose seeds are
  part done, and two releases.
- The three nits are fixed or answered.
- **Moves O4:** the retrospective says whether the work was aimed right, from evidence rather than
  recall.

## Affected

- **Area:** the retrospective and close's metrics.
- **Files & components:** `scripts/retro.py`, `scripts/metrics.py`, `scripts/sdlc.py` (retro's
  process figures), `docs/REFERENCE.md` *Retrospectives*, tests.
- **Downstream:** every host's retrospective.
- **Contracts:** retro is read-only but for its report; release, publish and measuring never read
  the register; the metrics trailer format is extended, never redefined.

## Constraints

- Metrics never read the register.
- The report template is `[review] irreversible`: the figures go in through the values retro
  already fills, as 162 did.

## Open questions

- ~~How a change with mixed signals is classed (a `fixes:` line plus a capability).~~ Resolved:
  the first of fix, capability, process, debt, with the others in `also` (spec R1).
- ~~What counts as "vanished" for a seed: retired without a change, or gone without a `Retire`
  line.~~ Resolved: gone with neither a `Close` nor a `Retire` record (spec R7).
