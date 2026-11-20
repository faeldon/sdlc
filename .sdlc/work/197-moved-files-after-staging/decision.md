DECISION: READY

**Why.** All five outcomes are built and tested. The new train tests run in the order a real landing does: resolver, then staging, then `--continue`. They cover UD and DU, with the carried file edited or staged. The deleted-`UU` refusal and the evidence pin also have tests. All four reviewers passed in round 1, the gate is green (3477 passed), and nothing is left but three nits and one pre-existing fence gap, which is written down in `notes.md`. Nothing in the rounds suggests the intent was wrong. The one departure from the plan, moving `_rebasing()` into `factory.py` because of `tests/test_modules.py`, is explained in the builder's report and checked by the code and security reviewers.

**Open items**
- None. All four findings are `recorded` with nothing left to do: F1 (code), F2 (security, pre-existing), F3 and F4 (test).

**Decisions to confirm**
- None. There is no `decisions.md`, no blocking line and no open default.

**For the person at ship**
- Look first at `plugins/factory/scripts/landing.py`, `cmd_resolve()` `--continue`. It is a sensitive path. Check the new `gone` and `staged_gone` checks and the `_neither_side()` test for `carried`. Then look at `plugins/factory/scripts/factory.py: deleted_sides()`, where the fallback reads the commits only while `_rebasing()` is true. Paths that are still in the index (staged as kept) are subtracted.
- Security's Medium note is pre-existing, not something this change opened. A moved file the resolver deletes still passes the fence, but `carried` names it, so the review sees it.
- The intent's outcome "`/sdlc-factory:land 194` lands without a hand step" can only be shown by running that landing. The train test is the closest proof the build has.
- This change touches no published interface.

- IMPACT: patch — a train's `resolve --continue` now accepts a correct modify/delete resolution whose deletion is staged, and refuses a deleted both-modified file. No command, flag or file shape changed.

**Undone items**
- UNDONE: pre-existing: plugins/factory/scripts/landing.py:1384: `_stray()` lets through any entry whose worktree column is blank, so it can't tell a fully staged edit or deletion by the resolver from one the replayed commit made. The resolver has `Bash`, and only its prompt says "reads only". It could `git add` an edit to any file, or `git rm` a file only `HEAD` holds, and `--continue` would stage it into the rebased commit, which then lands on the base. This change's new `staged_gone` check closes only the deletion case, and only for files `REBASE_HEAD` still holds. The fix: compare each staged path (`git diff --cached --name-only HEAD`) against `REBASE_HEAD`'s own paths (`git diff-tree -r --name-only REBASE_HEAD^ REBASE_HEAD`) plus the conflicted, moved and record files, and refuse any other. → bug: med: plugins/factory/scripts/landing.py: resolve --continue lets a resolver's fully staged edit or deletion outside its files into the rebased commit

  `med` is the guide's word for "its output is wrong and there is a way round it": the guide's own rule re-reviews a resolved conflict at the run's depth.

**How to recover**
- No line needed: the diff touches none of the irreversible paths (`defaults/`, `templates/`). The plan's Rollback still holds: `git revert` undoes it all.
