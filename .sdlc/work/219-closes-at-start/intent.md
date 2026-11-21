---
id: 219
slug: closes-at-start
tier: 1
impact: patch
stage: shipped
created: 2026-11-21
opened: 2026-11-21T14:25Z
updated: 2026-11-22
shipped: 2026-11-22
idea: 2026-11-21-42
depends_on: [216]
serves: [O6]
origin: self
---

# 219 — The issues a change closes are fixed at `start`, not read from its own branch

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

From nit 2026-11-20-47 (the security review of 202-defaults-to-landing):
`plugins/factory/scripts/factory.py` `intent_closes()` reads `closes:` from the branch's own
`intent.md`, while the sensitive bar is read from the base branch. A build can edit its own
intent and change what it may carry: dropping `closes:` removes the `issue` signal and lets a
default be carried with `- CONFIRM:` on a change that closes a public issue.

215-evidence-exits tried the fix and left it, carried forward as seed 2026-11-21-42: "Record the
intent's `closes:` at `start` in the records ledger, and have `intent_closes()` read the union of
it and the working copy (nit 2026-11-20-47, done right)." 216-autopilot's D9 now leans on
`closes:` being carried too, so the issue signal must not be something a build can remove.

## Outcome

- `factory.py start` appends the intent's `closes:` to the records ledger in the git common dir,
  once per run, before any agent runs.
- `intent_closes()` returns the union of the ledger's record and the working copy: a build can add
  an issue, never drop one.
- A test edits `closes:` out of an intent mid-run and checks `no_confirm_why()` still names the
  issue, and that `land-check`'s `issue` signal still fires.
- **Moves O6:** what a change closes is fixed before the agents run, so the gates that hang on it
  can't be loosened from inside the build.

## Affected

- **Area:** the factory's records and its landing signals.
- **Files & components:** `plugins/factory/scripts/factory.py` (`cmd_start()`, `intent_closes()`),
  the records ledger's line shape and `scripts/factory_records.py`'s pinned copy if core reads it,
  `plugins/factory/scripts/landing.py` where `land-check` reads it, the factory's tests.
- **Downstream:** the approver's `CONFIRM` rule, `land-check`'s signals, 216's autopilot.
- **Contracts:** the records ledger's format (extended, never redefined); `[review] sensitive`
  read from the base branch.

## Constraints

- The ledger is append-only, and its writer appends before it writes, as every vouched record is.
- A change with no `closes:` writes nothing new and behaves as today.

## Open questions

- A restart or an upgrade runs `start` again: is the union over every record of the change, or only
  the latest run's?
- Does core (the board, `status`) read the new line, so its copy in `factory_records.py` is
  pinned, or is it the factory's alone?

## Approach

At `start`, after the refusals, append a `closes` line for the change to `RECORDS_LEDGER` with the
intent's value (only when it has one). `intent_closes()` reads every such line for the change and
unions it with the working copy's value. Tests as above.

Nits taken in: 2026-11-20-47
