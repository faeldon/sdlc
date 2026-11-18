---
id: 143
slug: ship-review-parity
tier: 2
impact: minor
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: [2026-11-18-2, 2026-11-18-3, 2026-11-18-4, 2026-11-18-5]
depends_on:
serves: none
---

# 143 — Ship reviews a hand-built change as deeply as the factory reviews its own

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

114-one-review left four gaps, carried forward when it shipped:

- 2026-11-18-2: "ship checks only secrets, plus the fresh reviewer on a sensitive path; it has no
  security pass at the depth of the factory's `reviewer-security`."
- 2026-11-18-3: "ship never runs the spec's path end to end, as the factory's
  `reviewer-behaviour` does at landing."
- 2026-11-18-4: "ship has no UI review of a change that renders a page, where the factory runs
  `reviewer-ui` when `[ui]` is set."
- 2026-11-18-5: "ship has no UX review, where the factory runs `reviewer-ux` when `[ui]` is set."

So a change built by hand can reach `main` checked less than the same change built by the
factory. Today's landings showed what those passes catch: 124's ui and ux findings, 125's
behaviour finding.

## Outcome

- `/sdlc:ship` runs a security pass on a diff touching a sensitive path or a trust boundary.
- On a Tier 2 with a spec, ship runs the spec's path end to end, with its evidence.
- With `[ui]` set and a diff touching its paths, ship runs a UI and a UX review from the
  screenshots `factory.py` takes.
- Each finding is in `findings.md` in its section shape, and ship's question names the passes that
  ran. A test per pass checks it runs only when its condition holds.

## Affected

`skills/ship/SKILL.md` and its side files, `agents/reviewer.md` or new core agents,
`scripts/sdlc.py`'s `cmd_preflight()` (which passes run, as `branches`), `docs/REFERENCE.md` and
the ship evals. Every host's ship.

## Constraints

- Ship never pushes; its one WAIT and its question come from `preflight --question`.
- The core plugin's agents have no write tools.
- A pass that can't run (no `[ui]`, no screenshots) says so and is no stop.
- Ship's `SKILL.md` line budget holds: what only some runs need goes in a side file `preflight`'s
  `branches` names.

## Open questions

- ~~Does the core plugin get its own security, behaviour, ui and ux agents, or borrow the
  factory's when `sdlc-factory` is installed?~~ Resolved: its own read-only `sdlc:security`,
  `sdlc:ui` and `sdlc:ux`; the behaviour check is ship's own session (spec R8, R15).
- ~~How much paid review should ship add to a hand-built change by default?~~ Resolved: at most
  three agent calls on a deep diff that renders a page, none on a plain change, no opt-out
  (spec R2–R4, R16).
- ~~Does running the spec's path at ship replace `checks.md`, or sit beside it?~~ Resolved: beside
  it; the behaviour check never runs `checks.md` (spec R15).
