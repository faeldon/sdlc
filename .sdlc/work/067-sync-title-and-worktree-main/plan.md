---
id: 067
slug: sync-title-and-worktree-main
kind: plan
created: 2026-11-16
updated: 2026-11-16
---

# 067 — Close the small gaps in sync and worktree setup · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `_tracker_change()` hands the tracker `issue_title`, the heading with its id
  stripped by `TITLE_ID_RE`, which is what `new` gave the issue. `cmd_new`'s worktree line also
  prints the main checkout, and the `worktree_setup` config comment names `{main}`.
- `scripts/trackers/github.py`: `_view()` reads `title` by default. `sync()`, after the body edit,
  runs `gh issue edit --title` only when the issue's title differs, adding `title` to `done`, or
  reporting the failure as `error` with the body edit standing.
- `skills/intent/SKILL.md`: Step 5 replaces `{main}` with the main checkout's path, read from
  `new`'s worktree line, where it replaces `{worktree}`.
- `docs/REFERENCE.md`: the `worktree_setup` placeholder line names `{main}`.
- `tests/conftest.py`: the fake `gh`'s `issue edit` takes `--title`.
- `tests/test_archive.py`, `tests/test_skills.py`, `tests/test_sdlc.py`: the tests below.

## Work order

1. Add `issue_title` and the retitle in `sync()`, add the fake `gh`'s `--title`, write the three
   sync tests, and run `tests/test_archive.py -k sync`.
2. Print the main checkout on `new`'s worktree line, edit the intent skill, REFERENCE and the
   config comment, then add the skill and `new` tests.
3. Run `./check.sh`.

## Tests

- Retitle: a sync after the heading changes sets the issue's title, without its id, and `done`
  says `title`.
- No needless call: a sync with the heading unchanged makes no `--title` edit.
- A refused title edit: sync exits 1 with the error, and the body is updated all the same.
- `{main}`: the intent skill's Step 5 names it, and `new --worktree` prints `main checkout <root>`.

## Rollback

`git revert <sha>`. Nothing outside the repo is written. Issue titles already retitled on GitHub
keep their new titles, which match their intents.
