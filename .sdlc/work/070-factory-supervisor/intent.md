---
id: 070
slug: factory-supervisor
tier: 2
impact:
stage: build
created: 2026-11-17
updated: 2026-11-17
idea: 2026-11-17-5
depends_on:
serves: [O6, O3]
---

# 070 — A supervisor that runs a factory change and calls the person only when needed

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

A factory change makes its person start each stage by hand: `/sdlc:intent`, then
`/sdlc-factory:spec`, then `/sdlc-factory:build`, then `/sdlc:ship`, each a command they type and a
gate they answer. Inside the run, `/sdlc-factory:build` already carries the builder, the reviewer
rounds, the verifier and the approver after one WAIT, pausing only for a blocking `decisions.md`
entry, so the stops left are the handoffs between skills. `scripts/metrics.py`'s `REQUIRED` says
what that costs: a factory change owes 5 gates (`intent, spec, run, ship, close`) whatever its
tier, as many as a manual Tier 2 and two more than a manual Tier 1. The factory can't stop its
person less than building by hand, which is O6's promise turned around. And there is no measured
case: every one of the 68 `Close` commits in this repo with a mode says `Sdlc-Mode: manual`. Raised
by the retrospective of 2026-11-17 (seed 2026-11-17-5).

## Outcome

- One approved intent is carried through spec, build, review and verification to ready to ship
  by a supervisor, which the person takes from there.
- When the person asks, the supervisor carries several changes at once, each in its own worktree
  and branch, and the person still answers each change's calls one change at a time.
- The supervisor calls the person only for a gate the plugin's rules require, a blocking
  `decisions.md` entry, or the approver's ESCALATE. Everything the plugin's rules and the risk
  signals (`[review] sensitive`, `risk_paths()`) settle, it settles.
- Each call it makes to the person is recorded as a stop `metrics.py` counts, so a factory
  change's `Close` trailers say where it stopped.
- **Moves O6:** a factory change stops its person at intent, one supervisor gate, ship and close,
  plus each blocking decision or ESCALATE, and at nothing between spec, build, review and
  verification.
- **Moves O3:** the person answers one gate between an approved intent and ship on a factory
  change, and the supervisor stays free for their next request throughout.

## Affected

- **Area:** `plugins/factory/` (`sdlc-factory`), and the stop counting in `scripts/metrics.py`.
- **Files & components:** a new supervisor (an agent in `plugins/factory/agents/` or a skill in
  `plugins/factory/skills/`); `/sdlc-factory:spec` and `/sdlc-factory:build`, which it would drive
  or absorb; `factory.py`; `metrics.py`'s `GATES` and `REQUIRED` (`("factory", 1|2)`); the
  factory's tests; README's factory section.
- **Downstream:** every host with `sdlc-factory` installed: their factory runs change shape, and
  their retrospectives read `Sdlc-Totals`' `required`/`target` and `Sdlc-Mode: factory` against
  the old gate list. `sdlc` itself reads only the files a run leaves in the change's folder at
  ship, which must stay so. With several changes at once, the lock `claim()` takes and each
  change's own worktree are what keep them apart.
- **Contracts:** the factory's rules in `AGENTS.md` (agents that judge have no Write, only the
  builder edits, nothing commits, the person's decisions go through `decisions.md` asked by the
  build session); `sdlc` loads nothing from `plugins/` (`test_sdlc_loads_nothing_from_plugins`);
  one WAIT per writing skill, asked in a dialog; only the named steps push; the metrics trailer
  format is a contract, extended never redefined.

## Constraints

- Nothing that judges also edits: the supervisor edits no code, and only the builder changes
  code.
- Nothing commits or pushes: `/sdlc:ship` makes the one commit behind its own WAIT, and a
  supervisor never answers a gate for the person.
- A blocking decision and an ESCALATE always reach the person. Risk deepens a review, never skips
  one.
- Concurrent changes never share a worktree, a branch or a number, and a call to the person always
  names the change it is for.
- Existing `Close` trailers keep their meaning: a new gate list for factory runs is added beside
  the old one, so history's numbers still read.
- `factory.py` stays self-contained: no import of `sdlc.py`, copies pinned by tests.

## Open questions

- ~~Is the supervisor an agent in `plugins/factory/agents/` or a skill? A subagent can't ask the
  person (only the session's `AskUserQuestion` can), and the build skill already orchestrates from
  the session.~~ Resolved: a skill; the supervisor is `/sdlc-factory:build`'s long-running session
  in the main checkout, the chief of staff renamed (spec R1, R2).
- ~~How does it keep no Write while `decisions.md` entries and the run's files still get written,
  which the build session does today?~~ Resolved: the agents write in their own sessions and
  `factory.py agent` files their replies; the supervisor writes only the approved spec (R2, R5).
- ~~Which gates remain: does one supervisor gate replace spec's and run's (the yes then approving a
  spec it hasn't seen), or does spec's gate stay and the supervisor carry everything after it?~~
  Resolved: one gate per change, asked once its spec draft is shown (R8).
- ~~How are its calls recorded: `question` stops on a new `GATES` entry, or a new event kind, and
  what is the new `REQUIRED` row for factory runs?~~ Resolved: dialogs attributed to the change
  they name, `first_approval`, `REQUIRED` of `intent, run, ship, close` (R12, R13).
- ~~Does it stop at `/sdlc:ship`'s question, or run ship's preflight and review too, leaving only the
  WAIT?~~ Resolved: it stops at "ready to ship"; the person ships, in order, from the change's
  worktree (R10, R11).
- ~~With several changes at once: one session or one per change, how their calls to the person are
  queued, and how one change's ESCALATE or failure leaves the others running?~~ Resolved: one
  supervisor, every agent a background session in its change's worktree, each call naming its
  change, a stopped change leaving the others running (R3, R5, R9).
- ~~The seed's pilot, the first factory change in a host besides this repo with its `Close` numbers
  set beside this repo's manual medians: part of this change, or the next?~~ Resolved: deferred to
  after this lands; it is a run in another repo, outside this diff.
