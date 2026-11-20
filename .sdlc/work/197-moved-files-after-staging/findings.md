# Findings

> What a change's review found, one `## ` section a finding, committed with the change.
> `/sdlc:ship` writes it after every review, and the factory's `carry`, and its landing's rounds,
> write their agents' findings into it; `By:` names who raised one: `fresh` for ship's
> fresh-context reviewer, a factory role (`code`, `test`, …) for an agent, and no line on ship's
> own. A rerun keeps each id, marks one the diff no longer shows `fixed`, and never raises again
> one the person answered `wrong`, `intentional` or `minor`; an agent's `wrong` is its arbiter's,
> never the person's, and the same fault worded differently is one more. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:`, `By:` and `Fix:` lines, counts
> ship's own alone into the `Sdlc-Findings` trailer (its `agents=` says how many it left out),
> words ship's question from the ones proposed `fix`, and `ship` refuses while one is still `open`
> or `fix`. On a diff that touches a sensitive path, this note also says `Fresh review: ran`, or
> `Fresh review: skipped, <why>`. Each of ship's further passes that applies says the same on a
> line of its own: `Security review:`, `Behaviour check:`, `UI review:` and `UX review:`, and
> their findings' `By:` is `ship-security`, `ship-behaviour`, `ship-ui` or `ship-ux`, counted as
> ship's own (`passes=` says how many). A behaviour check that ran ends the file with an
> `## Evidence` section: each command on a `$ ` line, the tail of its output, then `exit: <n>`.

Fresh review: skipped, the factory's rounds stand in

## F1. [nit] [correctness] `staged_gone` calls `git cat-file` once per staged deletion; harmless, but you could read `REBASE_HEAD`'s tree once.

plugins/factory/scripts/landing.py:2829: `staged_gone` calls `git cat-file` once per staged deletion; harmless, but you could read `REBASE_HEAD`'s tree once.

Evidence: plugins/factory/scripts/landing.py:2829
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F2. [pre-existing] [contract] `_stray()` lets through any entry whose worktree column is blank, so it can't tell a fully staged edit or deletion by the resolver from one the replayed commit made.

plugins/factory/scripts/landing.py:1384: `_stray()` lets through any entry whose worktree column is blank, so it can't tell a fully staged edit or deletion by the resolver from one the replayed commit made. The resolver has `Bash`, and only its prompt says "reads only". It could `git add` an edit to any file, or `git rm` a file only `HEAD` holds, and `--continue` would stage it into the rebased commit, which then lands on the base. This change's new `staged_gone` check closes only the deletion case, and only for files `REBASE_HEAD` still holds. The fix: compare each staged path (`git diff --cached --name-only HEAD`) against `REBASE_HEAD`'s own paths (`git diff-tree -r --name-only REBASE_HEAD^ REBASE_HEAD`) plus the conflicted, moved and record files, and refuse any other.

Evidence: plugins/factory/scripts/landing.py:1384
Class: security review, round 1
Disposition: recorded
By: security

## F3. [nit] [correctness] nothing pins the guard in `deleted_sides()` that a path staged as kept (present in the index, changed on one side and deleted on the other) is not treated as a deletion.

tests/test_train.py: nothing pins the guard in `deleted_sides()` that a path staged as kept (present in the index, changed on one side and deleted on the other) is not treated as a deletion. Only the gone-from-index direction is tested.

Evidence: tests/test_train.py
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: med
By: test

## F4. [nit] [correctness] `_neither_side()` returns True when git can't hash a moved file, so a moved file that is gone from the tree counts as `carried`.

tests/test_train.py: `_neither_side()` returns True when git can't hash a moved file, so a moved file that is gone from the tree counts as `carried`. No test covers that case.

Evidence: tests/test_train.py
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
