---
id: 063
slug: close-warns-before-deleting
kind: plan
created: 2026-11-16
updated: 2026-11-16
---

# 063 — Close warns before its merge deletes files in the main checkout · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: a new `_ff_deletions(main, tree, trunk, branch)` after `_reaches()`, and one
  call in `cmd_close()` beside `reaches`, setting `report["deletes"]` for a shipped change not
  yet merged.
- `skills/close/SKILL.md`: Step 0 says what `deletes` holds, Step 1 shows both lists, and Step 2's
  question gains the deletion clause (ignored paths first, five at most, then `and N more`), or the
  `unknown` clause. It is unchanged when both lists are empty.
- `AGENTS.md`: a sentence in **Closing** naming `_ff_deletions()`.
- `tests/test_sdlc.py`: tests for R1 to R5, after `test_close_check_writes_nothing`.
- `tests/test_skills.py`: close's Step 2 names `deletes` and `now ignored` (R6).

## Work order

1. Write `_ff_deletions()`. Paths come from `_git(main, "diff", "--name-only", "-z",
   "--diff-filter=D", "--find-renames", trunk, branch)`, and None gives `unknown`. Ignored paths
   come from `git -C <tree> check-ignore --no-index -z --stdin` through `subprocess.run` (encoding
   utf-8), since exit 1 means none are ignored and `_git` can't tell that from a failure. Anything
   else gives `unknown`. The whole helper is wrapped in `try/except Exception`, as `_reaches()`
   is.
2. Call it in `cmd_close()` after the cleanup block: `if kind == "shipped" and not landed`.
3. Write the tests in `tests/test_sdlc.py` and run them.
4. Edit the close skill and add its test in `tests/test_skills.py`.
5. Add the AGENTS.md sentence, then run `./check.sh`.

## Tests

- R1, R4: `test_close_check_names_what_the_merge_deletes_from_the_main_checkout`. An untracked and
  ignored `data.db` is in `ignored`, a deleted `old.txt` is in `other`, `main` doesn't move, and
  `data.db` stays on disk.
- R2: `test_close_check_counts_a_rename_as_no_deletion`.
- R3: `test_close_check_says_nothing_deleted_as_empty_lists`, and
  `test_close_reports_no_deletions_once_merged_or_dropped`.
- R5: `test_close_goes_ahead_when_the_deletions_cant_be_read`. With `_git` patched to fail the
  diff, the report has `unknown` and the close returns 0.
- R6: an assertion on close's Step 2 in `tests/test_skills.py`.
- R7: `test_close_lands_removes_the_folder_in_a_commit_and_tidies` keeps its exact `done` list.

## Rollback

`git revert <sha>` undoes it all. The change writes nothing outside the repo and adds no config
key, so a revert leaves nothing behind: close's report just loses `deletes`, and its question goes
back to what it was.
