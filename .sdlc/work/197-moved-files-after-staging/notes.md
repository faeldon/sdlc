# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

- [x] pre-existing: plugins/factory/scripts/landing.py:1384: `_stray()` lets through any entry whose worktree column is blank, so it can't tell a fully staged edit or deletion by the resolver from one the replayed commit made. The resolver has `Bash`, and only its prompt says "reads only". It could `git add` an edit to any file, or `git rm` a file only `HEAD` holds, and `--continue` would stage it into the rebased commit, which then lands on the base. This change's new `staged_gone` check closes only the deletion case, and only for files `REBASE_HEAD` still holds. The fix: compare each staged path (`git diff --cached --name-only HEAD`) against `REBASE_HEAD`'s own paths (`git diff-tree -r --name-only REBASE_HEAD^ REBASE_HEAD`) plus the conflicted, moved and record files, and refuse any other. → bug: 2026-11-20-27
