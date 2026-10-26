---
id: 029
slug: close-records-base
tier: 2
impact:
stage: build
created: 2026-10-27
updated: 2026-10-27
idea: 2026-10-27-1
depends_on:
serves: [O4]
---

# 029 — Record where a change started, as Sdlc-Base

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`_change_base()` (`scripts/sdlc.py`) starts a change at the parent of the first commit holding its
`intent.md`. That is right only when that commit is the change's first, and nothing enforces it.
028 committed its three build steps without its folder, so the intent first appeared in the ship
commit `423d389`, and every reader of the start saw that commit alone:

- close's `reaches` said only "scripts", missing `bug`, `intent`, `retro`, `setup` and `ship`,
  which open sessions needed to reload;
- `measure`'s `Sdlc-Rework` wrote `final=2 rewrite=21600` instead of `final=100 rewrite=432`
  (amended by hand on `369fe51`);
- retro sizes a change and counts its rework from it (`retro()`), so it would read 028 as a
  2-line change;
- `bugs --introduced` would never blame a bug introduced in `4d17107` or `60373fa` on 028.

The branch's merge-base with `main` isn't a fix on its own: close fast-forwards `main` first, after
which it is the branch tip, and retro and bug blame read a change long after its branch is gone.

## Outcome

- Close notes where `main` was just before its fast-forward (the change's true start, since ship's
  `base` puts the branch on top of `main`) and writes it on the `Close` commit as
  `Sdlc-Base: <sha>`.
- `measure` (`final`/`rewrite`) and `reaches` use it: a test closes a change whose first commits
  don't hold its folder and asserts both see every commit.
- `_change_base()` reads `Sdlc-Base:` from the change's `Close` commit when there is one, falling
  back to the intent rule for closes from before it, so retro's size and rework and
  `bugs --introduced` see the whole change, and history needs no migration.
- **Moves O4:** a change built in several commits reads in retro with the size and rework of its
  diff from where it started, so the evidence retro sets direction from is right.
- 2026-10-27-1 is grouped in M5 (`.sdlc/DIRECTION.md`'s `Groups:` line).

## Affected

- **Area:** close (`cmd_close`'s merge and measure steps, `_reaches`), `_change_base()` and its
  callers (`_change_diff`, retro's sizes, `bugs --introduced`), the trailer format.
- **Files & components:** `scripts/sdlc.py`, `scripts/metrics.py` if the trailer is parsed there;
  tests for close, measure, retro and bugs; `docs/REFERENCE.md` (the trailers), AGENTS.md's
  metrics paragraph, `.sdlc/DIRECTION.md`.
- **Downstream:** every host's `Close` commits gain one trailer; retro and `bugs --introduced` in
  every host read it; older closes read as they do now.
- **Contracts:** "the event list and trailer format are a contract: extend them, never
  redefine" (this extends); measuring never refuses (a start that can't be found falls back,
  never fails a close); close's rerun-resumes rule (a rerun after `merge` must still know the
  start).

## Constraints

- A close that stopped after `merge` and is rerun recovers the same start, though `main` has
  moved; close resumes, it doesn't restart.
- Close never pushes; the trailer goes in the existing `Close` commit, not a commit of its own.
- A dropped change's `Drop` merge is unchanged: it measures nothing.
- `Sdlc-Fixes` and `Sdlc-Retired` are untouched.

## Open questions

- ~~How does a rerun of close find the start once `main` is fast-forwarded and the trailer isn't
  written yet: a reflog entry, a note in `.sdlc/` like the lock, or the change's first commit after
  the previous `Close` on `main`'s first-parent line?~~ Resolved: a ref, `refs/sdlc/base/<branch>`,
  written before the merge and removed with the branch (spec R1, R6).
- ~~Does `Sdlc-Base` belong with `metrics.py`'s measured trailers, or beside `Sdlc-Fixes`, written
  by `sdlc.py` and not measured?~~ Resolved: beside `Sdlc-Fixes`, so a failed measurement never
  drops it; `parse_trailers` reads it (R2, R7).
- ~~Should ship also warn when a branch's first commit doesn't hold the change's folder, or is the
  trailer enough?~~ Resolved: the trailer is enough; no warning.
