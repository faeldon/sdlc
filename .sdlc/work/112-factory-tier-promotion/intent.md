---
id: 112
slug: factory-tier-promotion
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-18
shipped: 2026-11-18
idea: 2026-11-17-76
depends_on: [111]
serves: [O6, O3]
---

# 112 — Promote a change to Tier 2 in the middle of a factory run

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

**2026-11-17-76:** 097 was promoted from Tier 1 to Tier 2 at its builder's blocking decision on
2026-11-17. But at `stage: build`, neither `/sdlc-factory:spec` nor the build skill drafts a spec:
both start from `plan` or `design`, and the builder rightly won't write one. So the supervisor
moved the stage back to `plan` by hand, ran the spec-writer, and resumed the builder with
`decided --decision D1`. The run's own records didn't say any of this had happened, and a
supervisor following the skill would have had no step to take.

## Outcome

- A change promoted to Tier 2 during a factory run has a path the script names: `factory.py` sets
  `tier: 2` and keeps the build so far, the spec-writer drafts the spec behind its own question,
  and the builder carries on from the approved spec.
- `verdicts` names the step (a `spec` next), and the build skill says what the supervisor does
  there; nothing is moved by hand.
- The run's records say the change was promoted, in which round and why, so the board and the
  approver see it.
- Tests in `tests/test_factory.py` pin the promotion: tier set, stage kept or moved as the spec
  says, spec drafted before the builder resumes, and no second promotion.
- **Moves O6:** a run that finds its change bigger than its tier finishes without a hand step.
- **Moves O3:** the person is stopped once, for the spec, not for the supervisor's fix-ups.

## Affected

- **Area:** sdlc-factory's build loop.
- **Files & components:** `plugins/factory/scripts/factory.py` (`verdicts`, `agent --task spec`,
  `decided`, `stage`), `plugins/factory/skills/build/SKILL.md`, the builder's prompt,
  `plugins/factory/README.md`, `tests/test_factory.py`.
- **Downstream:** every factory run; the board's step track; `/sdlc:ship`'s and the landing's
  reading of a Tier 2's `spec.md` and `plan.md`.
- **Contracts:** `TIER_ARTIFACTS` (a Tier 2 at `test` needs `spec.md` and `plan.md`); the spec is
  approved by a person, never written by an agent unseen; never patching an agent's reply.

## Constraints

- The promotion is the person's decision (a blocking decision's answer), never the builder's or
  the supervisor's alone.
- The spec still goes through its question before anything builds on it.
- `check --strict` passes at every stage the run leaves the change at.

## Open questions

- ~~Does the promoted run keep its rounds and its round limit, or start the count again after the
  spec?~~ Resolved: it counts again from the upgraded round, as a restart does (spec R6).
- ~~Is the builder's plan so far kept as `plan.md`, or rewritten against the new spec?~~ Resolved:
  kept, then rewritten by the resumed builder against the approved spec (spec R1, R8).
- ~~Can a run be demoted the other way, or is promotion one-way?~~ Resolved: one-way, and once
  (spec R5). The person renamed it an **upgrade** ("promote" also means a move between
  environments): `sdlc.py upgrade`, and an answer starting `upgrade to Tier 2` (R1 in
  `decisions.md`).
