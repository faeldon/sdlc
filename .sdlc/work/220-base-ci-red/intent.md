---
id: 220
slug: base-ci-red
tier: 2
impact: minor
stage: shipped
created: 2026-11-21
opened: 2026-11-21T14:25Z
updated: 2026-11-22
shipped: 2026-11-22
idea: 2026-11-21-36
depends_on:
serves: [O6]
origin: self
---

# 220 — A red CI on the base branch shows where the person looks

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

CI on `main` (`.github/workflows/check.yml`) was red from 9b21760 on 2026-11-17 until 214-ci-green
landed on 2026-11-21, four days and several landings, and nobody noticed: the local gate
(`./check.sh`) was green throughout, and neither `/sdlc:status` nor a landing's look says a word
about CI. 214 left it as its third open question, carried forward as seed 2026-11-21-36: "Say when
CI on the base branch is red, in a landing's look or in `status`, so the local gate isn't the only
word."

## Outcome

- `/sdlc:status` names a red (or failing to run) CI on the base branch's tip under *Problems*,
  with the commit and the run's link, and says nothing when it is green, pending, or no CI is
  known.
- `/sdlc-factory:land` and `/sdlc:ship` show it in the landing's look as a signal, so a landing on
  a red base is a choice the person sees.
- It reads CI through the tracker, never by core calling `gh`, and a host with no tracker or no
  CI sees nothing new.
- **Moves O6:** the person no longer learns of a red base from a release that fails days later.

## Affected

- **Area:** `status`, ship's preflight and the factory's `land-check`; the tracker interface.
- **Files & components:** `scripts/sdlc.py` (`status`, `preflight`), `scripts/trackers/github.py`
  and the tracker interface (CONTRIBUTING.md, *Writing a tracker*), `plugins/factory/scripts/landing.py`
  (`land_signals()`), docs/REFERENCE.md, tests.
- **Downstream:** every host on the GitHub tracker; the landing's auto-approval (a new signal can
  stop a batch that was `clear`).
- **Contracts:** core never calls `gh`; `status` is read-only and must stay fast; `land.auto`'s
  rule of what counts as a signal.

## Constraints

- No network call on every `status`: cached, as the update check is, or read only where it's asked.
- A CI the tracker can't read is unknown, never red.

## Open questions

- ~~Where the reading lives and how often it refreshes: a cache in the git common dir like
  `UPDATE_CACHE`, or a fresh call only at a landing?~~ Resolved: `sdlc-ci.json` in the git common
  dir, read again every 10 minutes for `status` and every 60 s for a landing (spec R3, R5, R7)
- ~~Does a red base stop an auto landing, or only show?~~ Resolved: it stops it, as a signal in
  `land_signals()` (spec R9)
- ~~Which runs count: every workflow on the tip, or a configured one?~~ Resolved: every workflow
  run on the tip's sha, with no new config key (spec R1)
