---
id: 017
slug: ship-seed-and-staged
kind: plan
created: 2026-10-25
updated: 2026-10-25
---

# 017 — Ship stages a path already staged, and finds the seed whatever form idea: takes · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `_status_entries(tree)` (new) returns `(xy, path)` from the porcelain parse
  `_dirty_paths()` does now, which returns their paths for its other callers; `_stage_change()`
  passes `git add --` only paths whose worktree column isn't a space, runs no `git add` with none,
  and reports every dirty path not left out; `_seed_title()` retries `IDEA_RE` on `## ` + the text
  and cuts only at ` → work/`. `_seed_lines()` unchanged.
- `skills/intent/SKILL.md`: Step 5's seed paragraph: `idea:` is the seed's title alone; only the
  heading's tag becomes `[building]`; the pointer is the entry's first body line.
- `defaults/SDLC.md`, `.sdlc/SDLC.md`: the `idea:` comment names a seed's title; `.sdlc/setup.json`
  re-recorded.
- `tests/test_sdlc.py`: the seed and staging tests below.

## Work order

1. Tests for R1–R5, failing first.
2. `_status_entries` and `_stage_change`, then `_seed_title`.
3. The intent skill; the SDLC.md comment in both copies; `sdlc.py record`.
4. `./check.sh`; `sdlc.py drift` clean.

## Tests

- R1: a committed `gone.txt` `git rm`'d and an edited file: ship exits 0, both staged, `staged
  gone.txt` printed.
- R2: a file staged and edited again: nothing of it left unstaged after ship.
- R3, R8: `[2026-10-02] [seed] Reopen drafts` joins the parametrized seed test; the host's pair
  (that `idea:` against a `[building] … → work/001-reopen-drafts/` heading) deletes that entry.
- R4: `Map intent → spec` is deleted, a `Map intent` seed beside it isn't.
- R5: a body line starting `[2026-10-02] [seed] Reopen drafts` is never taken for a heading.
- R6, R7: read in review; `tests/test_skills.py` and `tests/test_defaults.py` pass, `drift` clean.

## Rollback

`git revert <sha>`. Nothing outside the repo; hosts' seeds and `idea:` lines in the old forms read
the same either way.
