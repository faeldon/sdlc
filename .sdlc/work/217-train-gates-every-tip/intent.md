---
id: 217
slug: train-gates-every-tip
tier: 2
impact: patch
stage: shipped
created: 2026-11-21
opened: 2026-11-21T12:31Z
updated: 2026-11-21
shipped: 2026-11-21
idea:
depends_on:
fixes: [2026-11-21-43]
reworks: [139]
serves: [O6]
---

# 217 — Gate every landing train's tip, a train of one included

## Problem

A factory landing can push a red base branch while its question said the tip would be gated.
`_train_gate()` in `plugins/factory/scripts/landing.py` returns no gate for a one-change train
whose stacked commit equals its pre-train commit ("a train of one that never moved: gated as its
build was", from 139-landing-train). The build's gate isn't a gate of that commit, in two ways:

- **The build's gate ran on the uncommitted tree.** A new file stays untracked until the
  landing's `commit` step, so any check that reads `git ls-files` never sees it. On a host,
  2026-11-21, a change added a test file. The host's check that scans `git ls-files` for a
  forbidden pattern passed in every round, then failed on main once the file was committed (one
  test red). The train went `commit` → `close` with `"gates": 0`, close pushed, and main stayed
  red on origin until a hand fix.
- **The base can move between the build's gate and the landing.** `factory.py fresh` rebased the
  same change onto a newer base before the train began, merging another change's edits to a
  shared file. `pre` was recorded after the move, so `stacked == pre` still held and no gate ran
  on the merged tree. land-check had said "changed since its last review" and the commit carries
  `unreviewed=1`, but nothing gated it. Another one-change landing took the same `commit` →
  `close` path the same day.

The person's yes to `/sdlc-factory:land` approves "gated once at the tip", and for a train of one
that gate never runs, and the report doesn't say so.

## Outcome

- **Every train gates its tip as committed:** a one-change train runs the base branch's
  `[commands] check` on its committed, stacked commit before any close, like a longer train,
  recorded in `build/land-<n>.gate.md`. A red tip ejects the change, and the base branch is
  never pushed red by the train.
- **A test reproduces the bug:** a one-change train whose change adds a file that only a
  tracked-files check reads lands red today and is ejected after the fix.
- **The report is honest:** when a landing runs no gate (a base branch with no `check`), its
  JSON and Step 4 say so and why. `"gates": 0` never sits beside `done: true` unexplained.
- **The question still tells the truth:** "gated once at the tip" holds for every batch it's
  asked of, or the wording changes to say when no gate runs.
- **Moves O6:** a factory-built change escapes to the base branch no more often than one built
  by hand. A red main after a factory landing, as on a host on 2026-11-21, stops happening.

## Affected

- **Area:** the factory's landing train: `plugins/factory/scripts/landing.py` (`_train_gate`,
  the train's reading and report), the land skill's text where it describes the gate.
- **Files & components:** `landing.py`, its tests (`tests/` for the train), possibly
  `plugins/factory/skills/land/SKILL.md` and the landing question in `factory.py`.
- **Downstream:** every host that lands through `/sdlc-factory:land`. A one-change landing gets
  one more `[commands] check` run (minutes on a big gate), so it is slower by one gate.
- **Contracts:** the land skill's WAIT, which approves "gated once at the tip"; the records
  ledger, which vouches for each `land-<n>.gate.md`.

## Constraints

- Never push a base branch the train didn't gate as committed; a red tip ejects as today, never
  forces or leaves a half-landed state.
- A longer train's behaviour is unchanged: one gate at the tip, bisection on red.
- No second approval: the gate is what the existing yes already approves.
- The gate still uses the base branch's `[commands] check`, never the change's own copy.

## Open questions

- ~~Drop the shortcut outright, or keep it only when the recorded gate's tree provably equals the
  committed tree on the same base commit (tracked files included)? The second saves a gate but is
  easy to get wrong.~~ Resolved: drop it; the tree comparison is what failed (spec R1, Alternatives).
- Should the build's own gate count untracked files as tracked (e.g. `git add -N` before
  `[commands] check`), so a round's gate sees what the commit will hold?
- ~~Does `factory.py fresh` before a landing need to invalidate the round's gate for the landing's
  purposes, separately from this fix?~~ Resolved: no; every landing now gates its own commit (R1).
- Should a landing whose change carries `unreviewed=N` also run a landing review, not just a gate?
