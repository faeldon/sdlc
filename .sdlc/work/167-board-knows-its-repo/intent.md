---
id: 167
slug: board-knows-its-repo
tier: 2
impact: minor
stage: shipped
created: 2026-11-19
opened: 2026-11-19T01:18Z
updated: 2026-11-19
shipped: 2026-11-19
idea: 2026-11-18-66
depends_on:
fixes: [2026-11-18-103]
serves: [O2]
---

# 167 — The board knows which repo it shows, and when a landing runs unattended

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

A second repo's `/sdlc:dashboard` reports `serving: already` on 5170 when another repo's board
holds it: `_is_board()` (`scripts/board.py`) checks only `state.json`'s `"board": "sdlc"` marker,
never which repo the board shows, so a host's dashboard silently points at another repo's board and
the person reads the wrong changes. To see it: start a board in one repo with
`sdlc.py board --port 5170`, then run `/sdlc:dashboard` in another (bug 2026-11-18-103, introduced
by 075-factory-dashboard). Separately, the board infers an unattended landing from each change's
`runs/land-step.md` alone, so it can't tell a `train --run` loop that is live from one that died
mid-step; the run lock (`sdlc-factory-train-run.lock` in the git common dir) can (idea
2026-11-18-66, left undone by 147-landing-runs-unattended).

## Outcome

- `/sdlc:dashboard` reports `already` only when the board on the port shows the same repo root;
  another repo's board is a refusal naming the port, and the skill offers another `--port`. A test
  starts two fixture repos' boards and fails if the second reports `already`.
- The board's landing column says when a train loop is running unattended, read from the run
  lock, and never claims a live loop from `land-step.md` alone. A test holds the lock and reads the
  state.
- The board still writes nothing and serves `127.0.0.1` alone.
- **Moves O2:** no person acts on another repo's board thinking it's their own.

## Affected

- **Area:** the board and the dashboard skill.
- **Files & components:** `scripts/board.py` (`_is_board`, the `state.json` payload, the landing
  column), `skills/dashboard/SKILL.md`, possibly `scripts/factory_records.py` (if reading the lock
  counts as reading a factory record), `tests/test_board.py`.
- **Downstream:** every host's dashboard; the ui and ux reviewers join, since `board.py` is touched.
- **Contracts:** *The board* (writes nothing, serves `127.0.0.1`); *The factory* (the list of factory
  files `sdlc` reads, which gains the run lock); 163's rule that core reads factory records only
  through `factory_records.py`.

## Constraints

- The board keeps loading only when `board` runs, and never imports or runs `factory.py`.
- Reading the lock must not take it, or a landing would see the board as a second loop.

## Open questions

- ~~How the board identifies its repo: the main checkout's resolved path in `state.json`, or a hash
  of it, so the page doesn't show a home path.~~ Resolved: a hash, `repo_id` (spec R1).
- ~~Whether the run lock is read by trying a non-blocking lock (which briefly takes it) or by reading
  a pid or timestamp the loop writes into it.~~ Resolved: a non-blocking try, released at once and
  only while a train is under way, approved with the spec (R7–R10, *Contracts touched*).
