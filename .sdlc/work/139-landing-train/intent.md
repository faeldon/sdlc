---
id: 139
slug: landing-train
tier: 2
impact: minor
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: [2026-11-18-21, 2026-11-18-23, 2026-11-18-24]
depends_on:
serves: [O6]
---

# 139 — A landing train: the batch is integrated once, gated once, and its conflicts resolved once

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`/sdlc-factory:land` lands a batch one change at a time: each ships, rebases onto `main`, is gated
and reviewed again, and closes before the next starts, against a `main` that has just moved. From
the seed (2026-11-18-21): "Evidence 2026-11-18: four landing conflicts, two moves, and 131
re-conflicting in factory.py against 129 after a move." Every conflict costs a builder resolution,
a gate and every reviewer at the run's depth, and every move under a change another round. 134
removed the register's share; what's left is real code overlap, which a one-at-a-time landing
pays for once per change and again per move.

Close has a hazard the train must not widen (2026-11-18-23): "Close takes `_main_lock()` only
around its register write and `Close` commit, not from its merge: an `inbox-commit` that lands
between the two puts a `File` commit between the change's commit and its `Close`, where
`closed_changes()` reads the `Close`'s first parent as the change." And the test meant to cover
that lock (2026-11-18-24) "files the idea between close's check and its locked write, so it proves
the reread under the lock, not two processes racing for it."

## Outcome

- A landing of n changes stacks them, in `land-check`'s order, on one landing branch off `main`;
  one landing agent with every change's spec and diff resolves conflicts once across the batch.
- The base branch's gate runs once, at the stack's tip. A red tip is bisected and the change at
  fault ejected with its reason; the rest land, and nothing of the ejected one reaches `main`.
- `main` is fast-forwarded so each change's own commit is followed by its `Close` commit on the
  first-parent line: `closed_changes()`, release and retro read it as they read a one-at-a-time
  landing. A test lands a batch of three and walks `closed_changes()`.
- Close holds `_main_lock()` from its merge to its `Close` commit, so no `File` commit can come
  between them; a threaded test races `close` against `inbox-commit` for the lock, as `claim()`'s
  does.
- **Moves O6:** a batch landing spends one integration's gate and review on a batch, not one per
  change per move, and stops the person only where the stack itself failed.

## Affected

`plugins/factory/scripts/factory.py`'s landing (`land`, `land-check`, `resolve`, `land-verdicts`,
`gate --land`), `plugins/factory/skills/land/SKILL.md`, `scripts/sdlc.py`'s `cmd_close()`,
`_main_lock()` and `closed_changes()`, and the board's landing track (`scripts/board.py`), which
reads `runs/land-step.md`. Every factory host's landing changes shape; `/sdlc:ship` and
`/sdlc:close` by hand stay as they are.

## Constraints

- `main`'s first-parent line keeps one `Close` commit per change, right after the change's own
  commit.
- Never a merge of `main` into a branch, `--force`, or a stash; only the named steps push.
- Each change keeps its own commit, its `Sdlc-*` trailers and its `Close`.
- A conflict is resolved by an agent and reviewed again, never auto-accepted.
- The landing's one yes still covers exactly what's shown.

## Open questions

- ~~Who resolves a cross-change conflict: one landing agent, or each change's own builder in
  turn?~~ Resolved: one landing agent, the builder role's `train-resolve` task, with every
  change's spec and diff (spec R3).
- ~~Does bisection re-gate each half (log n gates), or eject by the files the failing tests
  touch?~~ Resolved: re-gate prefixes, at most ⌈log₂ n⌉ extra gates an ejection (spec R6).
- ~~Does an ejected change go back to its worktree as it was, or stay rebased onto the stack's
  base?~~ Resolved: back to its pre-train commit, with `reset --keep` (spec R7).
- ~~How does the board show a train: one track for the stack, or one per change?~~ Resolved: one
  per change, with `TRAIN: k of n` (spec R18).
- ~~Weigh, not require: run only the tests covering a move's untouched paths (the selective-tests
  note on 2026-11-18-21).~~ Resolved: weighed and not built (spec, *Boundaries*).
