---
id: 230
slug: nit-flow
tier: 2
impact: minor
stage: shipped
created: 2026-11-22
opened: 2026-11-22T01:39Z
updated: 2026-11-22
shipped: 2026-11-22
idea:
depends_on:
serves: [O3]
origin: self
---

# 230 — Nits are filed once, only while still true, and can be retired

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The register holds 64 nits against 23 ideas and no bugs, nearly all filed in the last four days:
each factory landing files up to `NIT_CAP = 5` (`factory.py:463`), and in one session on
2026-11-21/22, 219, 220, 221, 218, 222 and 225 filed about 18. A nit leaves only when a later
change names it on a `Nits taken in:` line, so the pile only grows. Much of it is noise, made by
how `cmd_carry` (`factory.py:2856`) weighs a round's nits:

- It keys a nit by reviewer and exact text, so a reworded repeat in a later round is a second
  nit: 221 filed `USES` and `VERSION` twice each ("`USES` still misses a quoted `uses:`").
- It drops a nit the build fixed only when it is `S` cost, `med` value and was handed to a
  rework; 221's `.yaml` glob nit was filed after its own restart had fixed it.
- A nit can't be retired: `RETIRE_REASONS["nit"]` is empty (`sdlc.py:7485`), and `/sdlc:idea`
  says a nit is ship's. A stale one (2026-11-21-55 names `216-autopilot/spec.md`, archived, which
  nothing will edit) or a duplicate stays until some change takes it in by hand.
- Every nit filed is a landing signal ("nits to file"), so a batch that files one never lands
  without asking: the noise costs a stop as well as a register line.

## Outcome

- A nit a later round of the same change raises again, reworded, is filed once.
- A nit the build fixed before the landing (no later round of its role raises it) is not filed,
  whatever its weights.
- `/sdlc:idea <id>` can retire a `[nit]` as `duplicate`, `stale` or `wontfix`, with a line on
  why, committed as `Retire <id>` like an idea's retirement.
- Each landing files fewer nits: by a lower cap, a value floor, or both (see Open questions).
- Today's duplicates and stale nits are retired by this change or by `/sdlc:idea` once it lands.
- **Moves O3:** fewer landings stop for a nit, and the register's nits are ones still worth doing.

## Affected

- **Area:** the factory's carry and landing, the register, `/sdlc:idea`.
- **Files & components:** `plugins/factory/scripts/factory.py` (`cmd_carry`'s weighing,
  `NIT_CAP`), `plugins/factory/scripts/landing.py` (`nit_findings`, the signal), `scripts/sdlc.py`
  (`RETIRE_REASONS`, `inbox-commit`), `skills/idea/SKILL.md`, `docs/REFERENCE.md`, the guide's
  nits rubric if the filing bar is stated there, and their tests.
- **Downstream:** every host: what a factory landing files into its register, and what
  `/sdlc:idea` may retire. The retro counts nits filed and retired.
- **Contracts:** a skill's WAIT (`/sdlc:idea`'s retire question now covers a nit); the
  register's rules (`inbox-commit` is the only code that commits it alone, and retiring needs a
  reason from `RETIRE_REASONS`); the `Sdlc-*` trailers if a retired nit is counted; ship's own
  nit filing, which `/sdlc:ship` does by hand for a change built there.

## Constraints

- No nit is dropped silently: one carry decides not to file still shows in `findings.md` with
  its reason, as `minor` ones do now.
- A nit an open change takes in can't be retired from under it.
- Release, publish and measuring still never read the register.

## Open questions

- ~~How does a landing file fewer: lower `NIT_CAP` (to 3?), file only `med` value and up, or
  both?~~ Resolved: a `med` value floor, `NIT_CAP` kept at 5 (spec R5).
- ~~How is "the same nit, reworded" told apart from a new one: same role and same `path:line`, or
  the reviewer marking a repeat?~~ Resolved: neither; a role's nits are filed from its last round
  only, and each reviewer is asked to raise its earlier nits again word for word (spec R1, R4).
- ~~Does `/sdlc:ship` (a change built by hand) follow the same filing bar?~~ Resolved: no, ship's
  person approves each nit it files (spec R12).
- ~~Is `stale` a reason of its own, or is it `wontfix`?~~ Resolved: its own (spec R7).
