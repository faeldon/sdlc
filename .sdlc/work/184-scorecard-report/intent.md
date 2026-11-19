---
id: 184
slug: scorecard-report
tier: 2
impact: minor
stage: shipped
created: 2026-11-19
opened: 2026-11-19T12:59Z
updated: 2026-11-19
shipped: 2026-11-19
idea: [2026-11-18-105, 2026-11-19-59, 2026-11-19-54, 2026-11-19-39]
depends_on:
serves: [O4]
---

# 184 — The retrospective report opens with the scorecard

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Waves 1 to 3 put every scorecard figure into `retro`'s JSON (lead time, work mix, follow-through,
autonomy, trust, cost, pipeline, surface, workarounds, by way of building), but the report a
retrospective commits still reads as the list of sections it had before them: a reader has to dig
the JSON for the scorecard. Scorecard S14, in the person's words: "the report opens with the Value
band, the five pillars' headlines and guardrails against the last retrospective (trend and n), and
the Trust band; each pillar's diagnostics follow in its own section."

Idea 2026-11-18-105 says how it reaches hosts: "the numbers in `sdlc.py retro` (core,
language-neutral), the page in `templates/retro.md` (a host overrides it in `.sdlc/templates/`),
the synthesis questions in a `guide/` file a host extends, and the metrics' meanings in
`docs/REFERENCE.md`'s *Retrospectives*", and "in a host, the Simplicity pillar means the process's
overhead and workarounds there; the plugin's own surface … is this repo's measure alone."

Three seeds on the same figures come in: 2026-11-19-59 (`by_way.throughput` floors the window at
one day, so a retro the day after the last one reports "196 factory changes a week"; a floor of a
week, or `per_week` null under a week, would read better), 2026-11-19-54 (`/sdlc:retro`'s passes
don't read `simplicity.workarounds`; its process pass could turn an `outside` or `restored` row into
a seed) and 2026-11-19-39 (an indicator `unit` of `—`, or a name or unit with stray spaces, reads
back from the report as a different key, so it gets no `last`). So do five nits on
`scripts/retro.py`: 2026-11-19-35 (`_cost()` computed twice), -42 (`_surface_at` on tags before the
registry, implicit), -43 (`retire.windows` below `RETIRE_AFTER` undocumented), -53 (`bisections` and
`accept_stops` have no `per_change`) and -60 (`introducer_way()` rescans history per bug).

## Outcome

- The committed report opens with the Value band, then each of the five pillars' headline and
  guardrail against the last retrospective, with its trend and `n`, then the Trust band; each
  pillar's diagnostics follow in a section of its own. Every figure comes from `retro`'s JSON, so
  the report and `sdlc.py retro` never disagree.
- A host gets the same page through `templates/retro.md`, which it can override; its Simplicity
  pillar shows its process's overhead and workarounds, never the plugin's own surface.
- The three seeds and five nits are fixed or answered.
- **Moves O4:** a retrospective opens with whether the work went well, in one screen, against the
  last one.

## Affected

- **Area:** the retrospective's report.
- **Files & components:** `scripts/retro.py` (`retro_report()`, `render_report()`),
  `templates/retro.md`, `scripts/indicators.py` (-39), `skills/retro/SKILL.md` (-54),
  `docs/REFERENCE.md` (*Retrospectives*), `docs/RETRO-SCORECARD.md`, `.sdlc/setup.json`.
- **Downstream:** every host's committed retrospective; a host's override of `templates/retro.md`.
- **Contracts:** `TEMPLATE_READS["retro.md"]` and `drift`'s `breaking` for any heading or
  placeholder the script reads; setup's record (`sdlc.py record`) when `templates/` changes; the
  report holds only what the script writes.

## Constraints

- No new figure: the report lays out what `retro` already computes.
- A figure with no data reads missing with its reason, never 0.
- A host's override without the new placeholders still renders, and `drift` says what it lacks.

## Open questions

- ~~Is the report one new template layout, or new placeholders inside the current one?~~ Resolved:
  a new layout, with only `{{scorecard}}` read back (spec R1, R11).
- ~~Which figure is each pillar's headline and guardrail, where the scorecard names more than one?~~
  Resolved: the pillar table in the spec's Design (spec R3).
