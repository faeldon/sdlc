---
id: 023
slug: branch-size
tier: 1
impact: patch
stage: shipped
created: 2026-10-25
updated: 2026-10-25
shipped: 2026-10-25
idea: A change's size counts every commit on its branch
depends_on:
serves: [O4]
---

# 023 — A change's size counts every commit on its branch

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`retro()` in `scripts/sdlc.py` measures each closed change with `git diff-tree --numstat` on
`rec["sha"]`, the one commit before its `Close`, not the change's whole branch. A change shipped as
two or more commits is sized by its last commit alone: 002, two commits and about 1,700 lines on
its branch, read as 1 file and 9 lines in the retrospective of 2026-10-24. The same per-commit file
list feeds `touched`, so rework misses every file an earlier commit on the branch touched. A
retrospective that sets direction from these numbers reads sizes that are too small and rework
that misses overlap.

## Outcome

- `retro`'s `files` and `lines` for a closed change count the branch's whole diff: from the base
  the change started on (the parent of the commit that added its `intent.md`, `_change_base()`)
  to the change's own commit before `Close`. A test with a two-commit change whose first commit
  holds most of the code shows both counted.
- Rework's `touched` set for a closed change comes from that same whole diff, so a file only an
  earlier commit on the branch touched still makes a later change rework it.
- A one-commit change reads as it did.
- **Moves O4:** the retrospective's sizes and rework pairs match what each change actually was, so
  direction set from "which changes were big" or "what keeps getting reworked" rests on true
  numbers: 002 reads as about 1,700 lines, not 9.
- Taken in: nit **012-1**. `nits_summary` compares `raised` as dates, so an entry with a malformed
  date is never its theme's oldest and `age_days` is not left null.

## Affected

- **Area:** the retro loop's counting in `scripts/sdlc.py`.
- **Files & components:** `retro()` (closed-change numstat), `_change_base()` (reused, perhaps
  taking a rev rather than a branch name), `nits_summary()`; tests in `tests/test_sdlc.py`.
- **Downstream:** `/sdlc:retro`, which reports sizes and rework. Rework pairs may rise, since
  `touched` grows to the whole branch, and the next retrospective's numbers aren't comparable with
  the last one's. Dropped changes already use the branch's whole diff (the `merge-base` of the
  `Drop` commit's parents) and are unchanged.
- **Contracts:** `closed_changes()` stays the one walk over landed changes; retro stays read-only;
  close's `Sdlc-*` trailers are untouched.

## Constraints

- The size comes from history alone: the same answer before and after close and on a rerun, as
  `_change_base()` already gives `_change_diff()`.
- A change whose intent-adding commit can't be found (history rewritten, a folder added by hand)
  never crashes retro, and falls back to something stated rather than a silent wrong number.

## Open questions

- ~~Should `lines` leave out the change's own `work/` folder and `.sdlc/last-id`, as
  `_change_diff()` leaves out the plugin's state, or count everything on the branch, as now?~~
  Resolved: everything, as now (a one-commit change counts its intent, and a dropped change counts
  everything); only the range changes. 002 reads as 18 files and 2,236 lines.
- ~~Is the fallback for a missing base the last commit's numstat (today's number) or `null` with a
  problem line?~~ Resolved: `files` and `lines` are null and a problem names the change. Rework's
  `touched` falls back to the last commit's files, so rework still sees something.

## Approach

In `retro()`, replace the `diff-tree` on `rec["sha"]` with `git diff --numstat --no-renames <base>
<rec["sha"]>`, where the base is `_change_base()` resolved against the change's own commit rather
than its branch name: the branch is gone after close, but the commit that added
`work/NNN-slug/intent.md` is on `main`. The file list feeds `files`, `lines` and `touched` as
before. Fix 012-1 by comparing `raised` values parsed as dates, skipping any that don't parse. Add
tests: a two-commit change sized whole, a rework pair found through a first-commit file, and a nit
with a malformed date that is not the oldest.
