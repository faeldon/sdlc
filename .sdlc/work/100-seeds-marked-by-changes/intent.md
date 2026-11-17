---
id: 100
slug: seeds-marked-by-changes
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: 2026-11-17-41
depends_on:
serves: [O3]
---

# 100 — Open changes mark their seeds without editing the register

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

From 2026-11-17-41: "Intent tags a change's seed `[building]` by editing the register on the change's branch, so every inbox commit on `main` while the change is open conflicts with it at rebase: 089, 090, 092, 094 and 095 all did on 2026-11-17." Each conflict was resolved by `sdlc.py resolve` or by hand, in the middle of a run or a landing. The seed's pointer ("Building in .sdlc/work/NNN-slug/.") lands on `main` only with the change, so the register on `main` never shows it anyway: `status` already reads open changes' `idea:` and `fixes:` lines (`_open_claims()`) to know which entries are taken.

## Outcome

- `/sdlc:intent` (single and batch) no longer edits the register on the change's branch: the `idea:` line alone marks a seed taken.
- `status`, the board, `nits`/`bugs` and `groups` show an entry an open change names as being built, from `_open_claims()`, with the change's number.
- `sdlc.py ship` still deletes the seed with the commit, as now.
- An old entry already tagged `[building]` on `main` still reads as before (read for good), and `check` accepts both.
- A test: an inbox commit on `main` while a change is open rebases the change's branch with no conflict.
- **Moves O3:** no change stops for a register conflict it didn't make.

## Affected

- **Area:** the register, intent and status.
- **Files & components:** `skills/intent/SKILL.md` and `batch.md` (Step 5's tagging), `scripts/sdlc.py` (`status`, `_open_claims()`, the register audit in `check`), `scripts/board.py` if it reads the tag, `docs/REFERENCE.md` (*`.sdlc/work/` and worktrees*), `defaults/`/`guide/` if they describe the tag.
- **Downstream:** every host's register and status; hosts with entries tagged `[building]` today.
- **Contracts:** the register is committed on its own only by `inbox-commit`; a file the plugin writes changes meaning (the `[building]` tag) — always Tier 2.

## Constraints

- An entry is never lost: a dropped change's seed shows open again with no edit.
- History's `[building]` tags keep reading.

## Open questions

- ~~Does the tag go entirely, or stay as something only `status` prints?~~ Resolved: nothing
  writes it; `status`, `bugs` and `nits` show the claiming change from `_open_claims()`, and
  legacy tags still read (spec R3, R4, R8). Plain `status` shows a count, `--all` the list (the
  person, at the run's question).
- ~~What does `/sdlc:drop` do with the seed now (today it un-tags it)?~~ Resolved: nothing; the
  tag never reached the base branch, and `stage: dropped` takes the change out of
  `_open_claims()` (spec R7). `inbox-commit` gains no refusal for updating a claimed entry (the
  person, at the run's question).
