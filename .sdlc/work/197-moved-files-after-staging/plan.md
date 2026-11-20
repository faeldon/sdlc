# 197 — Plan

> Tier 1 with a plan: the Approach reaches `factory.py`, `landing.py` and two test files.

## Files to change

- `plugins/factory/scripts/factory.py`
  - `deleted_sides()`: read the index once (`git ls-files --stage -z`). A modify/delete is a path
    whose unmerged stages are in `DELETED`, as now, or, mid-rebase (`REBASE_HEAD` resolves), one
    the commits show: deleted on one side since the merge base and changed on the other
    (`git diff --no-renames --name-only -z --diff-filter=D|M`). The second kind counts only when
    the path is gone from the index, so it is a staged deletion (the resolver's `git rm`, bug
    2026-11-20-23), never a file someone kept and staged. The deleting commit's `log` gets
    `--no-renames` too, so a split git calls a rename still finds the commit. Reuses `_git()`,
    `DELETED`, `COUNTER`, `work_rel()`.
  - `_rebasing()` moves here from `landing.py`, unchanged, so `deleted_sides()` reads the commits
    only while a rebase is under way (`REBASE_HEAD` outlives one) without factory calling into
    landing (`tests/test_modules.py`); landing and the tests call `factory._rebasing`.
  - `read_evidence()`'s docstring: a heading with no blank line before it doesn't end the
    section (nit 2026-11-20-21).
- `plugins/factory/scripts/landing.py`, `cmd_resolve()` `--continue`:
  - The missing-file pass (nit 2026-11-20-20): a conflicted file that is gone, or a staged
    deletion of a path the replayed commit (`REBASE_HEAD`) still holds, passes only when it is a
    `deleted_sides()` path; otherwise refused as a deletion outside a modify/delete.
  - `carried`: a moved file whose worktree content is neither `HEAD`'s nor `REBASE_HEAD`'s, not
    "has an unstaged edit", so a resolution the resolver staged is still named for the review.
  - The marker and `resolved` name the modify/delete paths even once staged.

## Work order

1. **The staged deletion passes** (bug -23): train test, resolver then `git rm` then
   `--continue`, UD and DU; then `deleted_sides()`.
2. **A staged carried file is still named**: the same test with the moved file `git add`ed;
   then `carried`.
3. **A deleted UU file is refused** (nit -20): train test over the README conflict, the file
   deleted (unstaged, and by `git rm`); then the missing-file pass.
4. **Evidence** (nits -19, -21): a test pinning the open section; the docstring.

## Tests

- `tests/test_train.py::test_a_staged_modify_delete_resolution_lands` (UD, DU; staged edit
  too): Outcome 1, 2, 3.
- `tests/test_train.py::test_a_deleted_both_modified_file_is_refused`: Outcome 4.
- `tests/test_evidence_headings.py::test_a_read_then_a_blank_heading_keeps_the_section_open`:
  nit -19.
- The 196 modify/delete tests still pass: unstaged resolutions are unchanged.

## Rollback

`git revert` undoes it all: nothing is written outside the code and tests.
