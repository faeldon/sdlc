---
id: 197
slug: moved-files-after-staging
tier: 1
impact: patch
stage: shipped
created: 2026-11-20
opened: 2026-11-20T01:57Z
updated: 2026-11-20
shipped: 2026-11-20
idea:
depends_on:
fixes: [2026-11-20-23]
reworks: [196]
serves: [O6]
---

# 197 — resolve --continue keeps a modify/delete resolution's moved files once it is staged

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Bug 2026-11-20-23: when a train's resolver settles a modify/delete conflict by carrying the deleted
file's edits into a file the deleting commit added, `resolve --continue` in
`plugins/factory/scripts/landing.py` refuses it: "edited outside its conflicted files: <that
file>". The allowed list comes from `deleted_sides()` in `plugins/factory/scripts/factory.py`,
which reads git's unmerged entries. By the time `--continue` checks, the deletion is staged and no
unmerged entry is left, so the moved list is empty and the carried file looks like a stray edit.
196 added that allowance, but its tests checked before staging, not in the order a real landing
runs. On 2026-11-20 the landing of 194 stacked on 193's edits to `tests/test_factory.py`. The
resolver carried 193's 69 new lines into `tests/test_factory_decisions.py`, correctly, and the
train still stopped at `resolve 194`.

Three nits from 196 sit on the same code: 2026-11-20-20 (security F2: the missing-file pass accepts
any gone conflicted path, so a resolver that deletes a both-modified `UU` file gets the deletion
staged without a word); 2026-11-20-19 (a read that printed output, then a blank line and a
`## Notes` heading with no `exit:`, keeps the Evidence section open); 2026-11-20-21
(`read_evidence()`'s docstring overstates how strict it is).

## Outcome

- `resolve --continue` allows the files the deleting commit added or changed, worked out from the
  rebase's own commit (`REBASE_HEAD`) or recorded before anything is staged, so a correct
  modify/delete resolution passes whether or not its deletion is already staged.
- A test fails if a resolution that stages the deletion and carries the edit into a moved file is
  refused, in the order a landing really runs it: the resolver, then the staging, then
  `--continue`.
- `/sdlc-factory:land 194` lands without a hand step.
- A conflicted file that is gone passes only when it is one side of a modify/delete conflict, never
  a `UU` one (nit -20).
- The two evidence nits are fixed.
- **Moves O6:** a train lands a change that moves or splits files, unattended.

## Affected

- `plugins/factory/scripts/landing.py` (sensitive: `cmd_resolve --continue`, `_stray()`).
- `plugins/factory/scripts/factory.py` (`deleted_sides()`, `read_evidence()`).
- `tests/test_train.py` and the evidence tests.
- **What reads it:** every landing train's resolve step, and every factory build's evidence check.

## Constraints

- The fence still holds: the resolver edits only the conflicted files and the deleting commit's
  added or changed files (196's D1, the person's call), and `--continue` decides it, never the
  prompt.
- A resolved conflict is still reviewed again at the run's depth.
- Evidence stays strict for a command that isn't a read.

## Approach

In `deleted_sides()`, or at `--continue`, take the moved list from the commit being replayed
(`REBASE_HEAD`'s added and changed files) and from git's record of the conflict, not from the
unmerged entries alone, so it survives the staging. Restrict the missing-file pass to those
deleted-side paths. Add a train test that runs resolver, then staging, then `--continue`. Fix the
evidence rule and its docstring.

Nits taken in: 2026-11-20-20, 2026-11-20-19, 2026-11-20-21

## Open questions

None.
