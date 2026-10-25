---
id: 023
slug: branch-size
kind: plan
created: 2026-10-25
updated: 2026-10-25
---

# 023 — A change's size counts every commit on its branch · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `_change_base()` takes an optional `rev`, so it can find a change's start
  from its own commit once the branch is gone. `retro()` sizes a closed change by
  `git diff --numstat <base> <sha>`: `files` and `lines` are null and a problem line is added
  when there's no base. `nits_summary()` compares `raised` as dates (nit 012-1).
- `skills/retro/SKILL.md`: the `changes` bullet says files and lines cover the whole branch and
  may be null.
- `tests/test_retro.py`: `_close()` gains `later=` (a second commit on the change). New tests for
  whole-branch size, rework through a first-commit file, and no base.
- `tests/test_nits.py`: a malformed `raised` date is never a theme's oldest.
- `work/023-branch-size/intent.md`: both open questions struck with the decisions below.

Decided in plan mode: size counts everything on the branch, `work/` included, as it does now (only
the range changes). When no commit is found that adds the intent, `files` and `lines` are null and
a problem names the change. Rework's `touched` then falls back to the last commit's files.

## Work order

1. `_change_base(main, branch, rev=None)`: log over `rev or branch`. Existing callers are
   unchanged.
2. `retro()`: whole-branch numstat for `files`, `lines` and `touched`, with the fallback.
3. `nits_summary()`: the date comparison.
4. Tests, then the retro skill's one clause, then strike the intent's questions.

## Tests

- Two-commit change: `files` and `lines` count both commits.
- Rework found through a file only the earlier change's first commit touched.
- No intent commit: `files`/`lines` are None, and a problem names the change.
- The existing one-commit size test (`files == 3`) passes unchanged.
- `nits_summary` skips `2026-00-01` for `2026-10-04`, with `age_days == 20`.
- Manual: `sdlc.py retro` from the worktree shows 002 as 18 files / ~2,236 lines.

## Rollback

`git revert <sha>` covers all of it. Retro is read-only and nothing is stored, so the next
`retro` run reads the old numbers again.
