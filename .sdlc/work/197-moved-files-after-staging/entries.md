# 197-moved-files-after-staging — entries

Retire 2026-11-20-19: taken in by 197-moved-files-after-staging
Retire 2026-11-20-20: taken in by 197-moved-files-after-staging
Retire 2026-11-20-21: taken in by 197-moved-files-after-staging

## [2026-11-20-27] [bug] resolve --continue lets a resolver's fully staged edit or deletion outside its files into the rebased commit

Found by the review of 197-moved-files-after-staging.
pre-existing: plugins/factory/scripts/landing.py:1384: `_stray()` lets through any entry whose worktree column is blank, so it can't tell a fully staged edit or deletion by the resolver from one the replayed commit made. The resolver has `Bash`, and only its prompt says "reads only". It could `git add` an edit to any file, or `git rm` a file only `HEAD` holds, and `--continue` would stage it into the rebased commit, which then lands on the base. This change's new `staged_gone` check closes only the deletion case, and only for files `REBASE_HEAD` still holds. The fix: compare each staged path (`git diff --cached --name-only HEAD`) against `REBASE_HEAD`'s own paths (`git diff-tree -r --name-only REBASE_HEAD^ REBASE_HEAD`) plus the conflicted, moved and record files, and refuse any other.

Severity: med
Paths: plugins/factory/scripts/landing.py

## [2026-11-20-28] [nit] `staged_gone` calls `git cat-file` once per staged deletion; harmless, but you could read `REBASE_HEAD`'s tree once.

Raised by the code review of 197-moved-files-after-staging, round 1: plugins/factory/scripts/landing.py:2829: `staged_gone` calls `git cat-file` once per staged deletion; harmless, but you could read `REBASE_HEAD`'s tree once.

Theme: robustness
Paths: plugins/factory/scripts/landing.py
Cost: S
Value: low
Raised by: 197-moved-files-after-staging (correctness)

## [2026-11-20-29] [nit] nothing pins the guard in `deleted_sides()` that a path staged as kept (present in the index, changed on one side and deleted on the other) is not treated as a deletion.

Raised by the test review of 197-moved-files-after-staging, round 1: tests/test_train.py: nothing pins the guard in `deleted_sides()` that a path staged as kept (present in the index, changed on one side and deleted on the other) is not treated as a deletion. Only the gone-from-index direction is tested.

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: med
Raised by: 197-moved-files-after-staging (correctness)

## [2026-11-20-30] [nit] `_neither_side()` returns True when git can't hash a moved file, so a moved file that is gone from the tree counts as `carried`.

Raised by the test review of 197-moved-files-after-staging, round 1: tests/test_train.py: `_neither_side()` returns True when git can't hash a moved file, so a moved file that is gone from the tree counts as `carried`. No test covers that case.

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 197-moved-files-after-staging (correctness)
