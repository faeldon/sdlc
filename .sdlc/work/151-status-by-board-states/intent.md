---
id: 151
slug: status-by-board-states
tier: 2
impact: minor
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: 2026-11-18-60
depends_on: [145]
serves: [O3]
---

# 151 — status groups its sections by the board's columns

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

In the seed's words: "status groups its sections by the board's columns (Planned, Designing,
Building, Ready, Landing, Needs you), so the board and status use one vocabulary. Raised by
145-escalations-that-clear, whose spec left status as it is: it reshapes status's output for every
host, a change of its own." Once 145 lands, the board says **Ready** and **Landing** while `status`
says *Ready to ship* and *Ready to close*, and a person reads two maps of the same work.

## Outcome

- `sdlc.py status` groups open changes under the board's six states, in the board's order, by
  `board.py`'s `column()` rule, never a copy that can drift; `■ What needs me` stays first, as
  "Needs you".
- `status --all`'s *Next up*, *Problems* and *Release due* sections are unchanged.
- A test places a hand-built and a factory change at each state and finds each under the same
  heading in `status` as its column on the board.
- **Moves O3:** a person reads one vocabulary for where work stands, so a glance at either `status`
  or the board says what to do next.

## Affected

`scripts/sdlc.py` (`status`), a shared reader with `scripts/board.py` if needed,
`docs/REFERENCE.md` (status's sections), `tests/test_sdlc.py` and `tests/test_board.py`. Every
host's `status`, and the `/sdlc:status` skill's reading of it. It waits on 145.

## Constraints

- `status` stays read-only and quick.
- `board.py` still loads only when `board` runs: a shared rule lives where both read it without
  `status` loading the board's server.
- Skills that read `status`'s sections by name (`/sdlc:status`, intent's Step 0) still find what
  they read, or change with it.

## Open questions

- ~~Does the shared rule move from `board.py` into `sdlc.py`, with the board calling it?~~ Resolved:
  yes, `column()`, `BY_STAGE`, `_seen()` and `_touched()` move to `sdlc.py` (spec R1, R2).
- ~~Do empty states print a heading?~~ Resolved: yes, with a count of 0 (spec R6).
- ~~Does `status`'s plain-text output keep its `■` markers?~~ Resolved: yes (spec R6, R8).
