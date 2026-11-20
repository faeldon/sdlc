---
id: 199
slug: landing-records-unforgeable
tier: 2
impact: minor
stage: shipped
created: 2026-11-20
opened: 2026-11-20T05:37Z
updated: 2026-11-20
shipped: 2026-11-20
idea: 2026-11-19-69
depends_on:
serves: [O6]
---

# 199 — Landing records an agent in the change's folder can't forge

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Seed 2026-11-19-69, left undone by 185: "gate/build/accept records are trusted by the hash they
state, which any agent that can write in the change's folder can write; a script-side signature or
a record kept outside the tree would close it" (`plugins/factory/scripts/landing.py:2180`). The
builder and the resolver both edit files in the change's worktree, and a landing that reads a green
`land-<n>.gate.md` or `land-accept.md` it didn't write would close a change whose gate never passed.

## Outcome

- A gate, build or accept record that the script didn't write is refused by the landing that reads
  it: a test writes a well-formed green record by hand and sees `land` or `train --run` refuse it.
- The records the board, `status` and the hand gate read still read the same.
- **Moves O6:** a factory landing's green gate is one the script ran.

## Affected

- `plugins/factory/scripts/landing.py`, `plugins/factory/scripts/factory.py`,
  `scripts/factory_records.py` (core's copies, pinned by `tests/test_modules.py`), `scripts/sdlc.py`
  (`cmd_gate()`'s hand-gate record), the train's state in the git common dir.
- **What reads it:** every landing, the board, `status`, `/sdlc-factory:decide`'s gate clearance.

## Constraints

- Records stay files a person can read in the change's folder.
- Nothing about a record goes into `sdlc.lock` or a tree other than the git common dir.
- Core never imports `factory.py`; each reads the other's files with pinned copies of its parsing.

## Open questions

- ~~A keyed signature (whose key, kept where?) or a ledger of record hashes in the git common dir?~~
  Resolved: a ledger in the git common dir; a key could only live beside it (spec, Alternatives
  rejected).
- ~~Does the hand gate's `build/gate.md` need the same protection, or only the landing's records?~~
  Resolved: yes, since a green hand gate clears the approver's `gate` reasons (spec, R6).
