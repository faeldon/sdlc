---
id: 029
slug: close-records-base
kind: spec
created: 2026-10-27
updated: 2026-10-27
---

# 029 — Record where a change started, as Sdlc-Base · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1. Close knows the start before it merges.** On a shipped change's first run, before
   `merge`, close writes `refs/sdlc/base/<branch>` at `git.base`'s tip (which its preconditions
   already require to be an ancestor of the branch). A rerun keeps the ref it finds and never moves
   it. Test: a close that fails at `archive`, rerun, still writes the first run's start.
2. **R2. The `Close` commit carries `Sdlc-Base: <full sha>`**, written by `remove folder` beside
   `Sdlc-Fixes`, from the ref; written even when `measure` failed; absent only when there is no
   ref. A dropped change's `Drop` commit gets none. Test: the `Close` commit's body has
   `Sdlc-Base:` naming where `main` was.
3. **R3. Close's own readers use it.** `_change_diff` (so `Sdlc-Rework`'s `final`/`rewrite`) and
   `_reaches` measure from the ref. Test: a change whose first two commits lack its folder, one
   touching `skills/x/SKILL.md`, closes with `reaches` naming `sdlc:x` and `final` counting both
   commits' lines.
4. **R4. `_change_base()` reads the trailer first.** Given a change's `Close` commit (a new
   `close` argument, passed from `closed_changes()`' records and from the `bugs --introduced`
   walk), it returns that commit's `Sdlc-Base:`; inside close, the ref; without either, the intent
   rule, unchanged, so older closes read as they do now. Tests: retro's size for such a change
   counts every commit; `bugs --introduced` blames a line from its first commit on it.
5. **R5. Nit 2026-10-25-18 is settled.** A change whose intent landed on `main` early is measured
   from where `main` was at its close, never across other changes' commits. Test: an intent
   committed to `main`, another change closed, then this one closed: its size excludes the
   other's.
6. **R6. The ref goes with the branch.** `delete branch` also deletes `refs/sdlc/base/<branch>`;
   a failure to delete it is noted, never a refusal. Test: no `refs/sdlc/base/*` remains after a
   clean close.
7. **R7. The trailer parses.** `metrics.parse_trailers` reads `Sdlc-Base` as `out["base"]`, a
   string; REFERENCE's trailers and AGENTS.md's metrics paragraph list it beside
   `Sdlc-Fixes`/`Sdlc-Retired`, as written by `sdlc.py`, not measured.
8. **R8. 028 gets its start by hand.** In the main checkout, before ship, `369fe51 Close
   028-remove-1-4-shims` is amended to add `Sdlc-Base: 158aa7251a64d0658883e27224b10a97d61703fd`
   and the seed commit `3338823` is re-applied on top; both are unpushed. Outside the change's
   diff; ship's `base` then rebases 029 onto the rewritten `main`. Check: `sdlc.py retro`'s size
   for 028 counts its three build commits.
9. **R9. M5 groups the seed:** `.sdlc/DIRECTION.md`'s M5 `Groups:` line gains `2026-10-27-1`.

## Design

Close reads `trunk`'s tip before the steps run (`before`, already computed). On a shipped change,
if `refs/sdlc/base/<branch>` is missing and the branch isn't yet on `trunk`, it creates it with
`git update-ref`; a rerun after the merge finds it there. `_change_base(main, branch, rev=None,
close=None)` becomes, in order: the `close` commit's `Sdlc-Base:` when given; the ref, while the
branch exists; today's rule (parent of the first commit holding the intent). `closed_changes()`
already holds `close_sha` and passes it (retro's size); `bugs --introduced`'s walk already has the
`Close` commit and passes it; `_change_diff` and `_reaches` run inside close and get the ref.
`_close_commit`'s trailers become `captured + base + fixes`, `base` being
`[f"Sdlc-Base: {sha}"]` from the ref. `delete branch` runs `branch -d` then `update-ref -d` on the
ref. `metrics.parse_trailers` adds `"base"` to the raw-string keys beside `mode` and `coverage`.

A ref under `refs/sdlc/` is git's own state: never pushed (publish pushes the branch and the tag
only), never dirtying a tree, never tripping a refusal.

## Contracts touched

- **Trailers are a contract, extended and never redefined:** `Sdlc-Base` is new; nothing existing
  changes.
- **Measuring never refuses:** the start isn't measured; a missing ref falls back to the intent
  rule and drops the trailer, never failing a close.
- **Close resumes:** the ref is written once and read on every rerun; `remove folder` already skips
  a commit written earlier, so there is no second trailer.
- **Only publish pushes:** the ref is local and nothing pushes it.
- **Never name `main` in a git call:** every new call uses `trunk`.
- **History rewritten (R8):** only unpushed commits on this machine, with the person's approval
  given at spec, and ship's `base` handles 029's branch.
- **Always Tier 2:** it changes what close writes into every host's history.

## Alternatives rejected

- **Committing the folder with the first build commit:** a practice nothing enforces, and against
  "nothing commits before ship".
- **The branch's merge-base with `main`:** equals the branch tip once close has fast-forwarded, and
  is gone with the branch.
- **A note file in `.sdlc/`:** dirties the main checkout and needs its own cleanup; a ref is git's
  own state.
- **The reflog:** expires and can be turned off.
- **A ship warning about a folderless first commit:** unneeded once close records the start.

## Verification

- `./check.sh`.
- In a scratch repo: build a change in two commits without its folder, ship, make close's
  `archive` fail and rerun it: `git log -1 --format=%B main` shows `Sdlc-Base:` naming the
  pre-merge tip, `reaches` lists the skill, `final` counts both commits, and no ref is left under
  `refs/sdlc/base/`.
- After R8: `git log --format=%B -1 <028's Close>` carries `Sdlc-Base: 158aa72…`, and `sdlc.py
  retro` sizes 028 at about 120 lines added, not 2.
