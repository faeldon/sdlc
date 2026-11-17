---
id: 128
slug: unmark-withdrawn-issues
tier: 1
impact: patch
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: 2026-11-17-89
depends_on:
serves: [O2]
---

# 128 — A full marking pass unmarks an issue whose record was withdrawn

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

116 left undone: "A full marking pass (close, `mark-triaged`) still leaves a core-marked issue whose
record went (an entry's `Issue:` line removed by hand) as `dangling` for triage, not unmarked:
close's pass runs between its Close commit and the push that closes the change's issues, so it
would need `closed_by()` on the unpushed commits to tell a just-fixed issue from a withdrawn one."

## Outcome

- In a full pass, a core-marked issue whose record is gone and that no unpushed commit closes is
  unmarked; one an unpushed commit closes is left for the push.
- A test covers both, and the plain `dangling` case.
- **Moves O2:** an issue withdrawn from the register stops showing as waiting on triage.

## Affected

- **Area:** intake: issue marking.
- **Files & components:** `cmd_mark_triaged()` and close's marking pass in `scripts/sdlc.py`,
  `recorded_issues()`, `closed_by()`; `tests/`.
- **Downstream:** what a host's GitHub issues show.
- **Contracts:** `recorded_issues()` is the one reader of the records; the record is committed
  before the issue is told.

## Constraints

- Nothing is unmarked on a guess.

## Open questions

- Is the unpushed range always `origin/<base>..<base>`, and what does the pass do with no tracking
  ref?

## Approach

In the full pass, gather `closed_by()` over the unpushed commits, and unmark a dangling issue only
when none closes it.
