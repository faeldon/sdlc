---
id: 198
slug: landing-stages-its-own-paths
kind: spec
created: 2026-11-20
updated: 2026-11-20
---

# 198 — A landing stages only the paths its change owns · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Nits taken in: 2026-11-20-28

Assumptions checked in the code. Mid-rebase, `git diff --cached` against `HEAD` is everything the
next commit would add to `HEAD`: the replayed commit's clean changes, its conflicted paths, and
anything someone staged since. `REBASE_HEAD` is the commit being replayed. It is one commit with
one parent, because a landing commits each change as one commit (`_amend_record()`) and a rebase
drops merges. `_status_entries()` skips a rename's old path. The resolver runs only git reads
(`agents/resolver.md`), but it has `Bash`, so its prompt is the only thing holding it to that.
`_settle_counter()` stages `.sdlc/last-id` only when it conflicted, which means `REBASE_HEAD`
changed it.

"`REBASE_HEAD`'s own paths" means every path `git diff-tree -r --root --no-renames REBASE_HEAD`
lists. A rename shows as its deletion and its addition.

R1. `resolve --continue` refuses a staged edit to a tracked path that is outside `REBASE_HEAD`'s
own paths, the conflicted files, the moved files (`deleted_sides()`'s `moved`) and the change's
landing records. The refusal names the path and says "outside its conflicted files". It writes no
marker, stages nothing, and leaves the rebase under way with the same conflicted files.
`test_a_staged_path_the_replayed_commit_doesnt_own_is_refused[edit]` fails without it.

R2. The same refusal applies to a `git rm` of a file only `HEAD` holds (one the change below it
added). `test_a_staged_path_the_replayed_commit_doesnt_own_is_refused[rm]` fails without it.

R3. The same refusal applies to a staged rename (`git mv`) of a file `REBASE_HEAD` didn't touch,
and it names the old path even when the new path is one `REBASE_HEAD` owns. Fails without it:
`test_a_staged_path_the_replayed_commit_doesnt_own_is_refused[mv]`.

R4. The same refusal applies to a new file the resolution staged (`git add` of a file that is
untracked). `test_a_staged_path_the_replayed_commit_doesnt_own_is_refused[add]` fails without it.

R5. Undo the staged path in each R1–R4 case (`git checkout HEAD -- <path>`, or `git rm --cached`
and delete for a new file) and the same resolution continues. The path the replayed commit staged
cleanly (`notes.txt` in `test_a_resolution_outside_its_files_is_refused`) still passes as the
commit's own. The `[*]` cases above and that existing test both assert it.

R6. A modify/delete resolution still continues, whether the deletion and the carried file are left
unstaged or staged by the resolver, for both UD and DU. In the DU case the moved file belongs to
`HEAD`'s side and so is not one of `REBASE_HEAD`'s own paths. These keep passing unchanged:
`test_a_modify_delete_conflict_reaches_the_resolver_and_lands[UD|DU]` and
`test_a_staged_modify_delete_resolution_lands[*]`.
`test_a_modify_delete_resolution_outside_the_moved_files_is_refused` still refuses `README.md`.

R7. These keep passing unchanged: a settled `.sdlc/last-id`
(`test_a_stack_conflicting_on_last_id_too_resolves`), a non-ASCII conflicted path
(`test_a_train_conflict_in_a_non_ascii_path_resolves`), and the resolve run's records
(`RESOLVE_RECORDS`, `runs/land-resolved`, `build/land-<n>.md`).

R8. The owned paths are read before the script stages anything (the register's dropped entries,
`files`, `carried`, the records). They are read only while a rebase is under way
(`factory._rebasing()`), never from a `REBASE_HEAD` a finished rebase left behind. If no rebase is
under way, `--continue` refuses before reading or staging anything, saying no rebase is under way.
If git can't list `REBASE_HEAD`'s paths or the staged ones, it refuses: it never passes everything.
`test_resolve_continue_with_no_rebase_under_way_is_refused` drives a stale `REBASE_HEAD` (a rebase
that finished) with a staged edit and fails without it.

R9. (nit 2026-11-20-28) `--continue` reads `REBASE_HEAD` once. A single `diff-tree` listing gives
both the owned paths and which of them `REBASE_HEAD` keeps, and `staged_gone` is built from that
listing. It never runs `git cat-file` for each staged deletion. Without it,
`test_resolve_continue_reads_rebase_head_once` fails: it records `factory._git` calls during a
`--continue` that has two staged deletions and asserts no `cat-file` call and one `diff-tree` call
on `REBASE_HEAD`. A `git rm` of a file both sides changed (`UU`) is still refused as a
modify/delete (`test_a_deleted_both_modified_file_is_refused[git-rm]`).

R10. `.sdlc/REVIEW.md`'s Pass 1, *The ways this repo's code fails*, holds the bullet **Git state
read after the step that changed it.**, worded as seed 2026-11-20-40 words it.
`tests/test_defaults.py` still passes (the block sits under a heading the guide has and restates
none of it). `grep -n "Git state read after the step that changed it" .sdlc/REVIEW.md` finds it.

R11. The docstrings of `cmd_resolve()` and `_stray()`, and the comment above the fence, say the new
rule: a staged path must be one of `REBASE_HEAD`'s own, a conflicted file, a moved file or a record.
No doc names `staged_gone`'s `cat-file` read. `plugins/factory/README.md`, `agents/resolver.md` and
`AGENTS.md` already say the resolver may change no other file "tracked or new", and they stay true.
A grep for `_stray`, `staged_gone` and `resolve --continue` across `*.md` turns up no claim that
has gone false.

## Design

All of this is inside `cmd_resolve()`'s `--continue` branch in `plugins/factory/scripts/landing.py`
and one new helper beside `_stray()`. `factory.py` is unchanged: `deleted_sides()` stays as it is.

**No rebase, no read.** The branch starts by refusing when `not factory._rebasing(root)`
("no rebase under way: nothing to continue", with a plain line telling the person to run git status
in its worktree). Today that case reaches `git rebase --continue`, fails, aborts, and reports "a
second conflict", which is wrong. More to the point, `REBASE_HEAD` outlives its rebase, so any later
read of it would be the class this change names.

**One read of `REBASE_HEAD` (R9).** A new `_replayed(root) -> dict[str, str] | None` in
`landing.py` runs `git diff-tree -r --root --no-commit-id --no-renames --name-status -z REBASE_HEAD`
through `subprocess.run` with `encoding="utf-8"`, never through `_git()`, whose strip takes a
leading character. It pairs the `-z` fields into `{path: status}`. `None` means git failed. The
owned paths are its keys. The deletions `REBASE_HEAD` keeps the file for are the paths whose status
isn't `D`. `staged_gone` becomes the staged deletions (`xy == "D "`) whose path is one of those.
That is the same set as today's `cat-file` test restricted to owned paths. An unowned staged
deletion no longer reaches `gone` and is refused by the fence below instead. Either refusal stops
the landing. The `gone`, `deletable` and marker checks keep their order and wording.

**The staged listing.** A new `_staged(root) -> list[str] | None` runs
`git diff --cached --name-only --no-renames -z` (index against `HEAD`, unmerged paths included),
read the same way. `--no-renames` means a `git mv` lists the old path as well (R3), which
`_status_entries()` would skip.

**The fence.** `stray` becomes the paths `_stray()` already reports (unstaged edits and untracked
files) plus every `_staged()` path that is not owned, not conflicted (`files`, or unmerged in the
status), not `moved`, and not one of `records`. Each path is listed once, in order. Both reads
happen where `_stray()` is called today, before any `git add`, so they see the index the resolver
left (R8). A `None` from either read refuses with "git couldn't read the index or REBASE_HEAD in
the change's worktree". The refusal keeps "edited outside its conflicted files: <paths>". Its plain
line changes the undo to "git checkout HEAD -- <path>, or git rm --cached and delete a new file",
which undoes a staged change as well as a worktree one.

**Edge cases.** For the counter, `_settle_counter()` stages it only when it conflicted, so
`REBASE_HEAD` owns it and no special case is needed. The register is in `files` when it conflicted.
`drop_entries()` writes it after the fence and the script stages it. The change's own folder paths
are `REBASE_HEAD`'s, because the change commit carries them. The records the resolve run writes
mid-rebase are in `records`. A path both sides changed identically isn't staged at all. Every path
comes from git's `-z` output and is compared with git's `-z` output or with `as_posix()` records,
which covers Windows and non-ASCII paths.

**Known limit, left for the person.** The fence works by path. A resolver that stages a different
text for a path `REBASE_HEAD` owns but that didn't conflict still passes. Every reviewer at the
change's depth reads the resolution, and the gate runs at the tip, but no script check covers it.
See the open questions.

### Boundaries

- **Always:** refuse before staging, with the rebase left under way, and name every path.
- **Asks first:** nothing new. A refusal is a stop for the person, as today.
- **Never:** resolve, unstage, or restore anything itself; touch `land`'s commit, `_amend_record()`
  or `_status_entries()`'s other callers; change `deleted_sides()`.

## Contracts touched

- **Only the builder and the resolver edit, the resolver only the files the conflict names, which
  `resolve --continue` checks** (AGENTS.md, *The factory*). This change narrows the check to what
  that sentence already claims. The sentence stays true and gets more accurate.
- **Never resolve a conflict but through the resolver or the person** (intent constraint). The
  script still only checks and stages what the resolution left, and refuses everything else. It
  never undoes anything itself.
- **The scripts run on Windows** (`tests/test_windows.py`). Both new reads are text-mode
  `subprocess.run` with `encoding="utf-8"`, without `shell=True`, and with no platform module. Paths
  are git's own `-z` text, compared with git's `-z` text or `as_posix()` records. The new tests are
  `needs_uv` like their neighbours and aren't marked `portable`.
- **Modules loaded by path / `landing.py` holds the landing's functions** (`tests/test_modules.py`).
  `_replayed()` and `_staged()` are called only from `landing.py`, so they live there. They reach
  `factory.py` only through `factory.<name>`.
- **`.sdlc/REVIEW.md` holds only this repo's answers** (`tests/test_defaults.py`). The bullet is
  about this plugin's landing and resolve steps, and it sits under the guide's *The ways this repo's
  code fails* heading. It is not a guide edit, so it needs no `sdlc.py record`.
- **`landing.py` is in `[review] sensitive`.** The review runs at full depth. Nothing in the design
  asks it to be lighter.

No invariant needs to change.

## Alternatives rejected

- **Add `--no-renames` to `_status_entries()` and widen `_stray()` to staged entries.** That would
  be one listing instead of two, but `_dirty()` and `_amend_record()` read the same function. Their
  rename handling would change for every landing, which is outside this change's scope. The
  separate `git diff --cached` read is local to `--continue`.
- **Check the staged text against what the replay alone would have produced** (closing the
  path-level limit). That needs a merge (`git merge-tree`) of each owned path for every
  `--continue`. It is more machinery than the intent's Outcome asks for, which is path-level. It is
  left as an open question, not built.
- **Share one guard with `land`'s commit** (the intent's first open question, and DIRECTION.md M20's
  "the landing's commits"). `land` commits through `sdlc`'s own `ship`, with no rebase under way and
  so no `REBASE_HEAD`. Its amend is already fenced to the change's folder by `_amend_record()`. A
  shared function would have no common input. That half of M20 is for the change that takes
  2026-11-19-69.
- **Allow `.sdlc/last-id` or the register by name.** Neither is ever staged unless it conflicted,
  so both are already owned or conflicted. A name in the allowed list would let a stray edit to
  them through.
- **Keep `staged_gone` with a `ls-tree REBASE_HEAD` set** (the nit's literal fix). That is one read,
  but it is a second listing of `REBASE_HEAD` beside the owned paths. The `diff-tree --name-status`
  read answers both questions.

## Verification

```bash
uv run --group dev pytest -q tests/test_train.py -k "resolv or staged or modify_delete or last_id or non_ascii or rebase_head"
uv run --group dev pytest -q tests/test_defaults.py tests/test_modules.py tests/test_windows.py
grep -n "Git state read after the step that changed it" .sdlc/REVIEW.md
./check.sh
```

What healthy output looks like:

- The four `test_a_staged_path_the_replayed_commit_doesnt_own_is_refused[edit|add|rm|mv]` cases
  pass, along with `test_resolve_continue_with_no_rebase_under_way_is_refused` and
  `test_resolve_continue_reads_rebase_head_once`.
- Every existing resolve, modify/delete, counter and non-ASCII test passes unchanged.
- The grep prints one line under Pass 1.
- `./check.sh` ends green: ruff clean, the format check clean, pytest all passed,
  `claude plugin validate --strict` passing.
- Reverting the fence alone makes the `[edit]`, `[add]` and `[rm]` cases fail. Removing
  `--no-renames` from `_staged()` makes the `[mv]` case fail.

