---
id: 063
slug: close-warns-before-deleting
kind: spec
created: 2026-11-16
updated: 2026-11-16
---

# 063 — Close warns before its merge deletes files in the main checkout · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1.** `sdlc.py close NNN --check`, for a shipped change not yet on the base branch, reports a
   `deletes` object: `ignored`, the tracked paths the fast-forward removes that the change's
   branch now ignores, and `other`, every other tracked path it removes. Each is sorted and in
   posix form. A test makes a change that stops tracking a file and ignores it, plus a second file
   it just deletes, and checks that each lands in its own list.
2. **R2.** A file the change renames is in neither list. A test checks this.
3. **R3.** A shipped change that deletes nothing reports `deletes` with both lists empty. A dropped
   change and a change already merged (a rerun) report no `deletes` at all, since neither
   fast-forward removes anything. Tested.
4. **R4.** Working out `deletes` writes nothing: no ref, no index, no file in either checkout.
   `test_close_check_writes_nothing` still passes with a deletion in the fixture.
5. **R5.** It never refuses. When git can't produce the list, `deletes` is `{"unknown": "<why>"}`
   and close still goes ahead. A test forces the failure.
6. **R6.** `skills/close/SKILL.md` Step 1 shows both lists in full. When either list is non-empty,
   Step 2's question adds a clause after the fast-forward. It names the ignored paths first, up to
   five in all and then "and N more", and the yes covers that deletion. With both lists empty, the
   question is unchanged, word for word. With `unknown`, the question says the deletions couldn't
   be listed.
7. **R7.** No new stop, no new git step and no restore. `cmd_close()`'s steps and their order stay
   as they are, and nothing writes to the deleted paths.

## Design

A helper, `_ff_deletions(main, tree, trunk, branch) -> dict`, sits beside `_reaches()` and follows
its never-refuse shape:

- **Which paths go:** `git diff --name-only -z --diff-filter=D --find-renames <trunk> <branch>`,
  run from `main`. Close only fast-forwards, and its preconditions guarantee a clean tracked tree
  in the main checkout, so each of these paths is a file git will remove there. `--find-renames`
  is explicit so a rename counts as a move, whatever the host's `diff.renames` setting. `-z` keeps
  unusual filenames intact.
- **Which are now ignored:** `git check-ignore --no-index -z --stdin`, run in the change's worktree
  (`tree`), which holds the branch's `.gitignore` files. Exit 1 means none are ignored, which is an
  answer, not a failure. Any other failure gives `unknown`.
- `cmd_close()` calls the helper after the refusals and before `steps` are built, only when
  `kind == "shipped" and not landed`. The result goes into `report["deletes"]`. `--check` and a
  real close build the report the same way, so the JSON shows the same field either way.

The close skill reads it the way it reads `cleanup` and `push`: Step 1 shows it, and Step 2 adds
the clause. For example:

> `…fast-forward main to it, deleting from the main checkout data/cache.db (now ignored) and 3
> other tracked files, archive it to…`

## Contracts touched

- **Close's WAIT (always Tier 2).** The question still approves the same action at the same
  moment. It now also names a consequence the yes already carried. Nothing is approved that wasn't
  approved before.
- **`--check` writes nothing.** Both git calls only read (R4).
- **The base branch is never written as `main`.** Every call takes `trunk`
  (`test_no_git_call_names_main_itself`).
- **The scripts run on Windows.** Calls go through `_git()`, which already sets
  `encoding="utf-8"`. There is no `shell=True`, and the paths are git's own posix output.
- **Close's destructive-flag rule.** No new flag, and no new step that writes.
- **The plugin's own repo.** The `--check` handoff runs `main`'s script, which won't have the field
  until this change lands. Close treats a missing `deletes` as nothing to say, so the first close
  after this one behaves as it does today.

## Alternatives rejected

- **Restore or back up the files after the merge.** The intent rules this out. Close would be
  deciding what the person's data is, and `close_cleanup` stays the person's own command.
- **Refuse to close while a deletion is pending.** That would block every refactor that deletes a
  file and add a stop (O3) for a case a clause in the existing question covers.
- **Name only the now-ignored paths.** That misses data a change untracked without ignoring it. The
  person chose to list everything, with the ignored paths first.
- **Warn at ship as well.** Deferred. Ship's diff already shows each `D`. Only close knows what the
  main checkout holds at landing time, and a ship warning would mean changing a second WAIT.
- **Compare the main checkout's files on disk.** Its tracked tree is clean, so git's diff already
  gives the exact list, without walking the filesystem.

## Verification

```bash
uv run --group dev pytest -q tests/test_sdlc.py -k "close"
./check.sh
```

Healthy output: the new tests for R1 to R5 pass alongside the existing close tests, and
`./check.sh` exits 0 (ruff, format, pytest and plugin validate). Running `sdlc.py close 063
--check` on this change's own branch then shows `"deletes": {"ignored": [], "other": []}`.
