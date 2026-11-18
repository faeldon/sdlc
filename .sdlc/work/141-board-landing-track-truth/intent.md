---
id: 141
slug: board-landing-track-truth
tier: 1
impact: patch
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: [2026-11-18-17, 2026-11-18-18, 2026-11-18-19, 2026-11-18-20, 2026-11-18-33, 2026-11-18-38]
depends_on:
fixes: [2026-11-18-32, 2026-11-18-39, 2026-11-18-27]
serves: [O6]
---

# 141 — The board shows a landing as it really stands, in words a person can act on

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

133 gave the board a landing track, and today's landings found where it misleads:

- 2026-11-18-32: "`_on_board()` keeps a shipped folder only when `ready_to_close()` lists its
  branch, and a stopped rebase detaches the worktree's HEAD, so the card vanishes exactly while
  the builder resolves the conflict" (138).
- 2026-11-18-39, and its duplicate 2026-11-18-18: "`factory.py accept` and `cases` record no step
  in `runs/land-step.md`, so the card still shows the build track until `land` ships it" (134,
  137).
- 2026-11-18-17: "A stopped landing shows on its card but keeps its column."
- 2026-11-18-19: a stopped landing on a card already at `shipped` reads `or /sdlc:ship 012 by
  hand`, where the way on is `/sdlc:close NNN`.
- 2026-11-18-20: "the stop reasons are still raw git or tool text": `HEAD isn't the landing's
  commit…`, `landed by=auto, and …`.
- 2026-11-18-33: an early `stuck` or `untestable` stop "reads on the board as a plain `approve`."
- 2026-11-18-27: a card reads "decide D1 in the factory's supervisor"; "a person doesn't know
  what the supervisor is or where to go". Since 137, `/sdlc-factory:decide NNN` is where.
- 2026-11-18-38: build rounds are labelled `R1`, `R2`, which clashes with requirements (R1–R17)
  and the ledger's `R<n>`.

## Outcome

- A shipped change whose landing rebase is stopped keeps its card, on the landing track at
  `rebase`.
- `accept` and `cases` record a landing step before `ship`, and the track shows it.
- A stopped landing moves its card to Needs you, its way on naming `/sdlc:close NNN` on a shipped
  card and `/sdlc:ship NNN` otherwise.
- Every landing stop reason has a plain line saying what failed and what to do, the raw text kept
  below it.
- An early stop shows `stuck` or `untestable` and why, on the card and in `runs/stopped.md`.
- A pending decision says `/sdlc-factory:decide NNN for D1`.
- Build rounds read `B1`, `B2` and landing rounds `L1`: display labels only, no file name changes.
- Each has a test in `tests/test_board.py` or `tests/test_factory.py`.
- **Moves O6:** what the board says about a factory change is true at every step, so the person
  trusts it without reading the files.

## Affected

`scripts/board.py` and `scripts/board.html` (cards, tracks, columns, labels),
`plugins/factory/scripts/factory.py` (`accept`, `cases`, the stop texts, `runs/stopped.md`), and
`scripts/sdlc.py`'s `needs_of()`, shared with `status`, if a stopped landing moves columns there.
The board alone reads most of it.

## Constraints

- The board writes nothing, serves `127.0.0.1` alone, and builds every node with `textContent`.
- Its copies of `factory.py`'s parsing stay pinned by tests.
- No record's file name or field changes; only what's shown.
- The train's own board steps (`TRAIN: k of n`, `stack`, `eject`) are 139's (its spec's R18), not
  this change's; this change keeps to the one-at-a-time track's gaps and leaves those lines to 139.

## Open questions

- Should `status` also move a stopped landing to "What needs me" (through `needs_of()`), or only
  the board?

## Approach

In `board.py`, keep a shipped folder whose branch `state()` already finds rebasing (`rebasing`).
Have `accept` and `cases` write a step to `runs/land-step.md` through the recorder the other
landing commands use, and add `checks` to `LAND_TRACK`'s positions. Move a card whose
`land-step.md` holds a stop to Needs you in `board.py` (whether `status` agrees, through
`needs_of()`, the build decides with a test). Give each stop text in `factory.py` a `plain` line,
as `SHIP_REFUSED` has. Read `stuck`/`untestable` from `verdicts`' record into the card and
`stop_text()`. Change the round labels in `board.html` from `R` to `B`, and point the decision
line at `/sdlc-factory:decide`. A test for each.
