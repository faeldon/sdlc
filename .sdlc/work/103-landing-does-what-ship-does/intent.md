---
id: 103
slug: landing-does-what-ship-does
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: [2026-11-17-35, 2026-11-17-36, 2026-11-17-39]
depends_on: [097]
serves: [O3, O6]
---

# 103 — The factory's landing does what ship does

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

A factory change lands through `/sdlc-factory:land` only when nothing in it needs a person beyond a yes, so on 2026-11-17 four of ten changes (086, 089, 090, 093) were shipped and closed by hand:

- **2026-11-17-35:** "`land-check` leaves out a change with `checks.md` or skills' cases in scope, because only a person may run them."
- **2026-11-17-36:** "A change with undone `notes.md` items is left out of a landing, and one with assumed decisions lands only after someone ticks them by hand."
- **2026-11-17-39:** "`/sdlc:ship` adds `How to recover:` to a commit that touches `[review] irreversible`, but a factory landing never runs ship's recovery step, so 092's `templates/direction.md` landed without one."

## Outcome

- The landing's question shows, for each change that has them: each acceptance check's name and command; the skills' cases in scope, with their cap; each undone note's proposed disposition (a seed or dropped); each assumed decision to confirm; and the `How to recover:` it composed for an irreversible path. A change with any of these is a signal, so its batch never passes itself.
- On the yes, the landing runs `sdlc.py accept` and `sdlc.py run-cases` for that change as ship does (a failure stops that change and those after it), writes the dispositions and confirmations, and puts `How to recover:` in the commit.
- `land-check` no longer excludes a change for any of these.
- Tests: a batch holding a change with `checks.md`, one with an undone note, one touching an irreversible path, lands through `factory.py` alone.
- **Moves O3:** no factory change needs `/sdlc:ship`; the person answers one question per batch.
- **Moves O6:** every factory change lands one way, with ship's evidence.

## Affected

- **Area:** sdlc-factory's landing.
- **Files & components:** `plugins/factory/scripts/factory.py` (`land-check`, `land`, the question's parts), `plugins/factory/skills/land/SKILL.md`, `plugins/factory/README.md`, `tests/test_land.py`, and `sdlc.py`'s `accept`/`run-cases`/`undone` only as called.
- **Downstream:** every factory landing; the `Close` commit's trailers.
- **Contracts:** a skill's WAIT, what it approves (always Tier 2); acceptance checks run only through `accept`; `run-cases` never in `ALLOW_RULES`, a skill's `allowed-tools`, `check.sh` or CI, and the person answers its prompt; `[review] irreversible` matched by the script (`risk_paths()`), read from the base branch.

## Constraints

- `accept` and `run-cases` keep their own permission prompts: the landing's yes approves running them, the harness still asks.
- A paid run's cost cap holds per change.
- `Sdlc-Landed: by=person` for any change landed this way.

## Open questions

- ~~One question for the batch, or a second question per change with checks or cases?~~ Resolved: one for the batch, listing each change's checks and cases; the harness still prompts on each run (spec R3).
- ~~Does `run-cases` in a landing run per change, or once over the batch's union of cases?~~ Resolved: per change, under its own $5 cap (spec R5). The person chose, at the run's question: no second cases run after a landing rebase; the approver proposes each undone note's disposition; a change with an irreversible path and no `- RECOVER:` stays excluded.
