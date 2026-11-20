---
id: 203
slug: approver-on-sonnet
tier: 1
impact: none
stage: shipped
created: 2026-11-20
opened: 2026-11-20T05:38Z
updated: 2026-11-20
shipped: 2026-11-20
idea: 2026-11-20-38
depends_on:
serves: [O5]
---

# 203 — Run the approver on Sonnet for one window

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Seed 2026-11-20-38 (raised by the retrospective of 2026-11-20): Opus is 88% of the window's spend
($214.93 of $243.53). The approver runs on Opus at $16.07 over 43 runs and 23 minutes, and reads and
decides without editing. One window on Sonnet would cost about a tenth as much, and its decisions
can be checked against this window's.

## Outcome

- `.sdlc/factory.toml` sets the approver's model to `sonnet` at both depths, with a comment saying
  it is a one-window trial from the retrospective of 2026-11-20 and what the next retrospective
  reads to judge it: READY changes that escaped, and ESCALATEs the person found empty.
- `factory.py config` and `start` show `approver` on sonnet in `models_at`.
- **Moves O5:** a factory change costs less, with no worse decision.

## Affected

- `.sdlc/factory.toml`.
- **What reads it:** every factory run's approver, from the base branch's file.

## Constraints

- Nothing in the plugin's defaults changes: this is this repo's own config.

## Approach

Set `[models]` (or the key `factory.py config` documents) for the approver at full and light
depth. Run `factory.py config` and check `models_at` names sonnet for the approver at both.
