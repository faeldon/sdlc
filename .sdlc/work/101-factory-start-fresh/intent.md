---
id: 101
slug: factory-start-fresh
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: [2026-11-17-40, 2026-11-17-43]
depends_on:
serves: [O6, O3]
---

# 101 — Factory builds start current and share the gate

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Two costs of running several factory builds in one day:

- **2026-11-17-40:** "Every run on 2026-11-17 started from a worktree branched hours earlier, so the supervisor ran `sdlc.py base` (or `resolve`) by hand on each before building, or the builder would have built on old code."
- **2026-11-17-43:** "With five runs in parallel on 2026-11-17, a gate that takes 40 s alone took up to 200 s, each `pytest -n auto` fighting the others for every core."

## Outcome

- `factory.py start` reports how far behind the base branch the change is, and `/sdlc-factory:build` brings it up to date (`sdlc.py base`, `resolve` on a conflict) before its first agent runs; a build never starts on a stale branch without saying so.
- A limit on concurrent gates (`factory.gate_jobs` in `.sdlc/factory.toml`, or a lock the gate waits on), with a default that keeps one gate running as today; a waiting gate says it is waiting, and its wait isn't counted in its time.
- Tests: `start` on a branch behind `main`; two gates with a limit of one run one after the other.
- **Moves O6:** a factory change is built and gated on current code, in its usual time.
- **Moves O3:** no hand `base` before a build.

## Affected

- **Area:** sdlc-factory's start and gate.
- **Files & components:** `plugins/factory/scripts/factory.py` (`start`, `gate`, config), `plugins/factory/skills/build/SKILL.md`, `plugins/factory/README.md`, `tests/test_factory.py`.
- **Downstream:** every `/sdlc-factory:build`; a host's `.sdlc/factory.toml` (a new key).
- **Contracts:** `base` is ship's named write before a WAIT, which only moves the change's own branch and prints the undo: the build gains the same write; a new config key whose default keeps today's behaviour.

## Constraints

- The update before a build moves only the change's own branch, never stashes or merges, and stops on a conflict it can't resolve.
- A lock never outlives its gate (a crashed gate releases it).

## Open questions

- ~~Does the build's approval cover the `base` before it, or is it said and done before the question, as ship does?~~ Resolved: before the question, in Step 0, as ship's `base` is, so the spec-writer drafts against current code; AGENTS.md's *Writes before a WAIT* names it as a fourth exception (the person, at the run's question; spec R6).
- ~~A count limit (`gate_jobs`) or a lock of one? Where does the lock live (the git common dir, as `_main_lock()`)?~~ Resolved: a count, `gate_jobs`, default 1, slots as OS locks under the git common dir with names of their own; the default runs gates one at a time, a change from today's unlimited that the person chose over keeping today's behaviour, to be said at ship; the hand gate keeps no slot, a later seed (the person, at the run's question; spec R7–R11).
