---
id: 172
slug: close-in-steps
tier: 2
impact: patch
stage: shipped
created: 2026-11-19
opened: 2026-11-19T02:21Z
updated: 2026-11-19
shipped: 2026-11-19
idea:
depends_on:
serves: none
---

# 172 — Close runs as named steps

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`cmd_close` in `scripts/closing.py` is 371 lines in one function: the merge, the archive, the
folder's removal, measure, register filing, the push and the cleanup, each with its own resume
logic. It is the sensitive code where a mistake costs a host's history, and its size makes every
review of it a long read (scorecard R6). 162 added lead time inside its measure step. Four nits sit
on these paths: 2026-11-19-2 (a factory change with no timed rows drops `ready_wait`: decision D1
of 162, answered, so this change retires it as answered), -3 (the broad `except Exception` hides
programming errors as `lead=failed`), -4 (`lead=bad-opened` for `opened` after `closed` has no test
of its own), and 2026-11-18-100 (the cases cost ceiling loses a cent to float error).

## Outcome

- `cmd_close` is a short sequence of named step functions in `closing.py`, each refusing and
  resuming as today.
- A pure move: `close --check` and close's output, trailers and commits are identical on the
  existing close tests.
- -3 and -4 are fixed, -100's ceiling is computed exactly, and -2 is retired as answered.

## Affected

- **Area:** close.
- **Files & components:** `scripts/closing.py`, `scripts/sdlc.py` (the ceiling), the close and
  archive tests.
- **Downstream:** every close, here and in hosts.
- **Contracts:** closing's rules (refuse rather than force, resume where a step stopped, the lock
  from merge to `Close` commit); `[review] sensitive`, so full depth.

## Constraints

- Every git step still refuses rather than forces, and a rerun still resumes where a step stopped.

## Open questions

- ~~Whether the steps share a small state object or keep passing today's locals.~~ Resolved: a
  `_Close` dataclass passed to module-level step functions (spec Design).
