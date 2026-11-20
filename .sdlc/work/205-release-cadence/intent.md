---
id: 205
slug: release-cadence
tier: 1
impact: none
stage: shipped
created: 2026-11-20
opened: 2026-11-20T05:38Z
updated: 2026-11-20
shipped: 2026-11-20
idea: 2026-11-20-35
depends_on:
serves: [O4]
---

# 205 — Say when this repo releases: once each wave has landed

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Seed 2026-11-20-35 (raised by the retrospective of 2026-11-20): forty-four changes closed since the
last retrospective and none was released; v1.10.0 is still the latest tag. So `time_to_users` has
nothing to measure (44 of 44 unreleased), and no change's **Moves** line can be checked against a
user. The plugin's guide already says when one is due (`status`'s Release due: 5 changes of minor
impact or more, a major one, or the oldest 14 days closed), and `status` said so for most of this
window. But this repo's process doc says nothing of how a wave and a release fit, and the person
chose to finish wave 6 before releasing, so the release is more stable.

## Outcome

- `.sdlc/SDLC.md` says when this repo releases: once each wave of milestones has landed, before
  the next retrospective, rather than as soon as Release due shows.
- The guide's slot for it is answered, not restated (`tests/test_defaults.py`).
- **Moves O4:** each retrospective has a release its users have had to read evidence from.

## Affected

- `.sdlc/SDLC.md`.
- **What reads it:** `/sdlc:intent`, `/sdlc:retro` and a person reading the process.

## Constraints

- `.sdlc/SDLC.md` holds only this repo's answers to `guide/process.md`, each under a heading the
  guide has.

## Approach

Find the guide's block on the release loop; write this repo's answer under the same heading in a
few lines, without restating the guide's Release due rule.
