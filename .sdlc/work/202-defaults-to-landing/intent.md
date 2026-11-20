---
id: 202
slug: defaults-to-landing
tier: 2
impact: minor
stage: shipped
created: 2026-11-20
opened: 2026-11-20T05:38Z
updated: 2026-11-20
shipped: 2026-11-20
idea: 2026-11-20-36
depends_on:
serves: [O3]
---

# 202 — An escalation of assumed defaults alone goes to the landing's question

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Seed 2026-11-20-36 (raised by the retrospective of 2026-11-20): the person kept the default the
agents assumed 18 of 18 times this window (0 changed, n=18). Yet an approver escalates a change
while any default is open, so each such change stops once more, at `/sdlc-factory:decide`, before
the landing's own question confirms its assumed decisions anyway: `its assumed decisions confirmed
as shown`. Nine of this window's 43 factory changes stopped for something the process could have
let through.

## Outcome

- When an approver's only open reasons are assumed defaults, the change is READY, and the landing's
  question shows each assumed default with what the build assumed, its yes confirming them.
- An assumed default that the approver can't weigh as safe (a sensitive path, a policy, a
  `closes:` issue) still escalates.
- `/sdlc:ship` from a worktree still shows every assumed default.
- **Moves O3:** a factory change whose only open calls are defaults stops its person once fewer.

## Affected

- `plugins/factory/agents/approver.md` and its prompt, `plugins/factory/scripts/factory.py`
  (`decisions`, `verdicts`, the approver's decision reading), `landing.py`'s `land-check` and the
  question it words, `plugins/factory/skills/decide/SKILL.md`, `plugins/factory/README.md`,
  `scripts/sdlc.py`'s `needs_of()` and the board's columns.
- **What reads it:** every factory run's decision, the board, `status`, the landing.

## Constraints

- Approval is per question: the landing's yes confirms only what it shows.
- An agent never ticks a decision the person didn't answer: the landing's yes is the answer.
- `Sdlc-Landed: by=auto` stays only for a batch with no signal; an assumed default is a signal.

## Open questions

- ~~Should the approver still write `ESCALATE` with a reason the script reads as "defaults only", or
  `READY` with a list of defaults carried to landing?~~ Resolved: `READY`, with a `- CONFIRM: D<n>:`
  line per carried default (spec, R1 and Alternatives rejected).
- ~~Does `/sdlc-factory:decide` keep a path for a person who wants to answer defaults before
  landing?~~ Resolved: yes, unchanged; `ask` lists every open line at `stage: test` (spec, R10).
