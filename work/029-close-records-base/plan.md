---
id: 029
slug: close-records-base
kind: plan
created: 2026-10-27
updated: 2026-10-27
---

# 029 — Record where a change started, as Sdlc-Base · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `BASE_REF`, `BASE_KEY`; `cmd_close` writes `refs/sdlc/base/<branch>` before
  `reaches` and the merge, `remove_folder` adds `Sdlc-Base:`, `delete branch` removes the ref;
  `_change_base(main, branch, rev=None, close=None)` reads the `Close` trailer, then the ref, then
  the intent rule; retro's size and `introducer` pass the `Close` commit.
- `scripts/metrics.py`: `parse_trailers` reads `base` as a string.
- `tests/test_archive.py`: the trailer, the ref's life, a rerun after a failed archive, a drop, a
  folderless first commit seen by `reaches` and `final`.
- `tests/test_retro.py`: size from `Sdlc-Base`; nit 2026-10-25-18's early intent; no trailer reads
  as today.
- `tests/test_bugs.py`: `introducer` blames a folderless first commit.
- `tests/test_metrics.py`: `parse_trailers` gives `base`.
- `docs/REFERENCE.md` (trailers), `AGENTS.md` (metrics and closing paragraphs),
  `.sdlc/DIRECTION.md` (M5 `Groups:`).
- Outside the diff: 028's `Close` commit on `main` amended with `Sdlc-Base` (R8).

## Work order

0. R8 from the main checkout: rebuild `369fe51` with the trailer and `3338823` on top with
   `commit-tree` (dates kept, trees identical), `update-ref` main with an old-value guard; then
   `git reset --keep` the worktree's branch onto it.
1. The ref and the trailer (R1, R2, R6, R7), the change's folder in this first commit.
2. The readers (R3, R4, R5).
3. Docs and the milestone (R7, R9).

Each step ends with `./check.sh` green and a commit on the branch.

## Tests

- R1: a close failing at `archive`, rerun, keeps the first run's start.
- R2: the `Close` body carries `Sdlc-Base: <pre-merge tip>`; a drop carries none.
- R3: a folderless first commit touching a skill shows in `reaches` and in `final`.
- R4: retro's size and `introducer` see the whole change; a `Close` without the trailer reads as
  before.
- R5: an early-committed intent with another change closed between excludes the other's lines.
- R6: no `refs/sdlc/base/*` left after a clean close.
- R7: `parse_trailers(...)["base"]`.
- R8: manual: `git log --format=%B -1` on 028's `Close`; `sdlc.py retro` sizes 028 at ~120 lines.
- R9: the direction doc's M5 line (read by status's next-up tests unchanged).

## Rollback

`git revert` of the change's commit restores the code. Not covered: `Sdlc-Base` trailers already
written on `Close` commits stay in history (older code ignores them), a leftover
`refs/sdlc/base/<branch>` is removed with `git update-ref -d`, and 028's amended `Close` commit
keeps its trailer.
