---
id: 098
slug: board-fixes
tier: 1
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: 2026-11-17-47
depends_on:
fixes: [2026-11-17-30, 2026-11-17-23]
serves: [O6]
---

# 098 — The board shows a change as it is

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The board (`scripts/board.py`) shows wrong or stale state in four ways:

- **2026-11-17-30:** "While `resolve` or a landing rebases a change, git lists its worktree as a detached `HEAD`, so the board can't match the worktree to its branch and the card vanishes until the rebase ends." Seen for 091, 090 and 095.
- **2026-11-17-23:** "`next_action()` returns `/sdlc:close NNN` before it looks at `problems`, so a card under Needs you names a close" (scripts/board.py:574-577).
- **2026-11-17-47:** "`sdlc.py board` loads `board.py` once, so after a change to it lands the running server shows the old behaviour (091 sat under Needs you until a restart picked up 086)."
- **Nit 2026-11-17-22:** "`_progress()` takes any `decision.md` as a finished run, so a change put back to `build` shows every step done in the Build column."
- In the person's words: "also print the bound port for board --port 0": `sdlc.py board --port 0` serves on the port the OS picks but prints `http://127.0.0.1:0/` (the board half of 2026-11-17-19).

## Outcome

- A change being rebased keeps its card, marked rebasing, its branch read from `rebase-merge/head-name`; a test rebases a change and reads the board.
- A card with a `problems` entry never names `/sdlc:close` as its next action; a test.
- The running board serves `board.py` as it is on disk: it reloads the module when the file changes, or says on the page that it is stale; a test changes the file under a running server.
- The step track reads `decision.md` only at the stages a run's decision belongs to; a change put back to `build` shows its steps undone.
- `board --port 0` prints the port it bound; a test.
- **Moves O6:** what the board shows of a factory run is what the run is.

## Affected

- **Area:** the board.
- **Files & components:** `scripts/board.py`, `scripts/sdlc.py` (how a worktree's branch is read, `worktrees()`), `tests/test_board.py`.
- **Downstream:** anyone watching `/sdlc:dashboard`; `worktrees()` is also read by `change_dirs()`, so a rebasing change's folder is found too.
- **Contracts:** the board writes nothing and serves `127.0.0.1` alone; it builds every node with `textContent`; its copies of `factory.py`'s parsing stay pinned by `tests/test_board.py`.

## Constraints

- Reading a rebase's branch never changes git state.
- A reload never serves a half-written `board.py`: a module that fails to load keeps the old one and says so.

## Open questions

- Reload `board.py` on change, or only flag the page stale? Reloading keeps it current; flagging is simpler and can't break a running server.
- Should `change_dirs()` and `status` also see a rebasing change through the same reader, or only the board?

## Approach

Read a detached worktree's branch from its `rebase-merge/head-name` (and `rebase-apply/head-name`) in `worktrees()`; check `problems` before the close in `next_action()`; gate `_progress()`'s `decision.md` on the stage, as 086 did for the column (takes in nit 2026-11-17-22); have `serve()`'s handler compare `board.py`'s mtime and reload or flag; print `server.server_address[1]` in `cmd_board()`. Tests in `tests/test_board.py`.
