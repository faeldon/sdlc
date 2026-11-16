---
id: 063
slug: close-warns-before-deleting
tier: 2
impact: minor
stage: shipped
created: 2026-11-16
updated: 2026-11-16
shipped: 2026-11-16
idea: 2026-10-25-7
depends_on:
serves: [O2]
---

# 063 — Close warns before its merge deletes files in the main checkout

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

A host reported this on 2026-10-25. A change stopped tracking some files on its branch: data the
host wanted kept out of git from then on, so the change ran `git rm --cached` and added the paths
to `.gitignore`. When `/sdlc:close` ran `merge --ff-only`, git saw that those paths were tracked at
`main`'s old commit but missing from the new one. It deleted them from the main checkout's working
tree, and the new ignore rule didn't stop it. The files are still in history, so they can be
recovered. But nothing tells the person they were deleted. `close --check` doesn't list them and
close's question doesn't name them, so the yes approves a deletion the person never saw. The first
sign is a missing local file, with no clue that close removed it.

Close's preconditions make the deletion certain. `cmd_close()` refuses a main checkout with
uncommitted tracked changes, so every file the merge drops is unmodified, and git removes it
without asking.

## Outcome

- `sdlc.py close NNN --check` reports the tracked paths that exist in the main checkout and that
  the fast-forward will delete. It's a new field in its JSON, listing the paths the branch now
  ignores apart from the rest, and empty when there are none.
- When the list isn't empty, `/sdlc:close` shows it in Step 1, and its WAIT question names those
  paths, so the yes covers them.
- A test builds a change that stops tracking a file the main checkout holds, and checks that
  `close --check` names it. A change that deletes nothing reports empty lists and gets close's
  question unchanged. A dropped or already-merged change has no such field.
- **Moves O2:** no host loses local files to a close it didn't know would delete them.

## Affected

- **Area:** close: `cmd_close()` in `scripts/sdlc.py`, and `skills/close/SKILL.md`.
- **Files & components:** `cmd_close()` (the report it builds before any write), close's Step 1
  and Step 2, tests in `tests/test_sdlc.py`. `docs/REFERENCE.md` too, if it documents close's
  JSON.
- **Downstream:** every host that closes changes. People read close's question, and the close
  skill reads the `--check` JSON. A dropped change's close is unaffected: `Drop` is a `-s ours`
  merge that changes no files in `main`'s tree.
- **Contracts:** close's WAIT (the AGENTS.md rule on a skill's WAIT, always Tier 2). The `--check`
  JSON gets a new field beside the existing ones and redefines none of them. `close_cleanup` stays
  opt-in.

## Constraints

- Close still never restores, moves or backs up the files for the person. It reports them, and
  what happens next is the person's call. It must not become an automatic `after_close` step, and
  `close_cleanup` remains the only host command close runs.
- `close --check` stays read-only. Working out the list must not touch the main checkout or any
  ref.
- Close doesn't add a stop. The list goes into the question close already asks (O3).
- Every git call uses `trunk`, never `main` (`test_no_git_call_names_main_itself`). Paths are
  compared as `as_posix()`.
- The handoff in the plugin's own repo (`_handoff()`) still works: `--check` runs under main's
  script and reports the same field.

## Open questions

- ~~Which deletions should it name: every tracked path the merge removes, or only the ones the
  branch's `.gitignore` now ignores (data kept but no longer tracked)? Listing all of them also
  lists ordinary file deletions from a refactor, which the person approved at ship. Listing only
  ignored ones is quieter but misses data a change stopped tracking without ignoring it.~~
  Resolved: all of them, the now-ignored ones listed apart and named first (spec R1, R6).
- ~~Should a long list be capped in the question (the first few, then "and N more"), with the
  full list in Step 1?~~ Resolved: yes, five in the question, the full list in Step 1 (spec R6).
- ~~Should ship's question flag the same paths earlier, while the change can still be reworked, or
  is close the right single place?~~ Resolved: close alone for now. Ship's diff already shows the
  deletions, and a second WAIT change is deferred (spec, Alternatives rejected).
- ~~Does `/sdlc:release` or `/sdlc:publish` have the same blind spot anywhere they move a
  checkout?~~ Resolved: no. Release commits and tags without merging, publish only pushes, a
  `Drop` is `-s ours` and changes no files, and `base` moves only the change's own branch.
