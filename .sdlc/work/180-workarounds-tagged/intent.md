---
id: 180
slug: workarounds-tagged
tier: 2
impact: minor
stage: shipped
created: 2026-11-19
opened: 2026-11-19T07:58Z
updated: 2026-11-19
shipped: 2026-11-19
idea: 2026-11-18-93
depends_on: [174]
serves: [O4, O3]
---

# 180 — Workarounds are recorded, so the retrospective counts them

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The scorecard's Simplicity pillar counts process overhead and workarounds (S6): "a change landed
outside the loop, a record fixed by hand, an override, each recorded so retro counts it." None is
recorded today. This session alone had a register entry restored by hand after a landing retired
it, a train stopped and relaunched to drop a fix, and an ejected change landed again with a fix,
and no record says any of them happened.

Idea 2026-11-18-93 comes in: five changes' Important findings shared one class, where "a context or
reference doc still states a rule the change altered, or one place restates a rule changed in
another (072 F1, 077 F1, 127 F1, 128 F1 and F2, and 130 F1)". It proposes a bullet for
`.sdlc/REVIEW.md`, *The ways this repo's code fails*: "**A doc's claim the change made false.** A
sentence in `AGENTS.md`, `docs/REFERENCE.md`, `docs/CONTRIBUTING.md` or a README that names the
function, the command or the rule this diff changed, and still says what it did before. Grep the
docs for each name the diff touches."

And nit 2026-11-19-26: `measure.errors` (`scripts/closing.py`) holds the raw exception text; say in
the docstring that the message is for the person running close and must never become a trailer.

## Outcome

- Each kind of workaround is recorded where it happens:
  - a commit on the base branch that no change, inbox commit or release made;
  - a register entry restored or a record edited by hand;
  - an override (a train stopped, a change ejected, or a fix the person asked for at landing).
- `retro` counts each kind, with its `n`, under Simplicity.
- `.sdlc/REVIEW.md` names the doc-claim failure class.
- The nit is answered.
- **Moves O4:** the retrospective shows where the process got in the person's way.
- **Moves O3:** each workaround is a stop the process didn't plan for, so counting them shows where
  stops can fall.

## Affected

- **Area:** close, the register's commits, the factory's landing records, and the retrospective.
- **Files & components:** `scripts/closing.py`, `scripts/metrics.py` (if a trailer is added),
  `scripts/retro.py`, `plugins/factory/scripts/landing.py` (overrides), `.sdlc/REVIEW.md`,
  `docs/REFERENCE.md`.
- **Downstream:** every close; a host's retrospective; ship's and the factory's review, which
  read `REVIEW.md`.
- **Contracts:** metrics' trailers (extended, never redefined); `[review] sensitive` covers
  `closing.py` and `landing.py`, so full depth; `.sdlc/REVIEW.md` holds only this repo's answers
  to the guide.

## Constraints

- Recording a workaround never blocks it: the person can still do what they needed.
- A hand edit is detected from history where possible, never by asking the person to log it.

## Open questions

- ~~Which workarounds can be read from history alone (a base-branch commit no command made), and
  which need a record written when they happen?~~ Resolved: all but ejections and stops, read
  from 174's `runs/ejections.jsonl` (spec R1–R6).
- ~~Does the review bullet belong in `.sdlc/REVIEW.md` alone, or in `guide/review.md` for every
  host?~~ Resolved: `.sdlc/REVIEW.md` alone (spec R9).
