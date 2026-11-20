---
id: 198
slug: landing-stages-its-own-paths
kind: plan
created: 2026-11-20
updated: 2026-11-20
---

# 198 — A landing stages only the paths its change owns · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/landing.py`: in `cmd_resolve()`'s `--continue` branch, refuse first when
  `factory._rebasing()` is false; two new readers beside `_stray()`: `_replayed()` (one `git
  diff-tree -r --root --no-commit-id --no-renames --name-status -z REBASE_HEAD`, `{path: status}`)
  and `_staged()` (`git diff --cached --name-only --no-renames -z`), both `subprocess.run` with
  `encoding="utf-8"`, never `_git()`; `staged_gone` built from `_replayed()` (no `cat-file`); the
  fence adds every staged path not owned, not conflicted, not moved, not a record. Docstrings of
  `cmd_resolve()` and `_stray()` and the fence's comment say the new rule. Reuse: `_status_entries()`,
  `_stray()`, `UNMERGED`, `factory._conflicted()`, `factory.deleted_sides()` (unchanged),
  `_land_refused()`.
- `tests/test_train.py`: `test_a_staged_path_the_replayed_commit_doesnt_own_is_refused[edit|add|rm|mv]`,
  `test_resolve_continue_with_no_rebase_under_way_is_refused`,
  `test_resolve_continue_reads_rebase_head_once`.
- `.sdlc/REVIEW.md`: Pass 1 bullet *Git state read after the step that changed it.*, as the seed
  words it.
- Docs: `plugins/factory/README.md`, `plugins/factory/agents/resolver.md`, `AGENTS.md` already say
  "no other file"; reread, edit only a claim gone false. No `factory.py` change.

## Work order

1. **The fence over staged paths (R1–R5, R7).** Parametrised test first, red for edit/add/rm (passed
   today) and mv (refused today as a modify/delete, not as outside). Then `_replayed()`, `_staged()`
   and the fence; the undo half of each case continues.
2. **`staged_gone` from the one listing (R6, R9).** Test that records every git argv during a
   `--continue` with two staged deletions; red on today's `cat-file`. Then rebuild `staged_gone`
   from `_replayed()`. The modify/delete tests and `[git-rm]` stay green.
3. **No rebase, no read (R8).** Test with a finished rebase (its `REBASE_HEAD` left behind) and a
   staged edit; red today (it reports "a second conflict" after writing a marker). Then the refusal
   at the top of `--continue`.
4. **Docs (R10, R11).** REVIEW.md bullet; docstrings; grep the `*.md` for `_stray`, `staged_gone`,
   `resolve --continue`.

## Tests

- R1–R4, R5: `test_a_staged_path_the_replayed_commit_doesnt_own_is_refused[edit|add|rm|mv]`, each
  refused naming the path, "outside its conflicted files", no marker, rebase under way, README
  still conflicted; undone, the same resolution continues. R5's clean replay:
  `test_a_resolution_outside_its_files_is_refused` (unchanged).
- R6: `test_a_modify_delete_conflict_reaches_the_resolver_and_lands[UD|DU]`,
  `test_a_staged_modify_delete_resolution_lands[*]`,
  `test_a_modify_delete_resolution_outside_the_moved_files_is_refused` (unchanged).
- R7: `test_a_stack_conflicting_on_last_id_too_resolves`,
  `test_a_train_conflict_in_a_non_ascii_path_resolves`, the land tests in `tests/test_land.py` that
  record mid-rebase (unchanged).
- R8: `test_resolve_continue_with_no_rebase_under_way_is_refused`.
- R9: `test_resolve_continue_reads_rebase_head_once`; it records every git command
  `subprocess.run` gets (`_replayed()` reads through `subprocess.run`, never `factory._git()`, as the
  spec's design says), and asserts no `cat-file` and one `diff-tree` naming `REBASE_HEAD`.
  `test_a_deleted_both_modified_file_is_refused[git-rm]` unchanged.
- R10: `tests/test_defaults.py`, and the `grep` in `checks.md`.
- R11: read by the reviewers; the grep in the spec's Verification.

## Rollback

`git revert` undoes all of it: nothing is written outside the repo, no data or published name
changes. A landing refused by the new fence leaves its rebase under way, as every refusal did.
