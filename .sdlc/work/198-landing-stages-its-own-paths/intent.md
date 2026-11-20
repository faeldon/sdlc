---
id: 198
slug: landing-stages-its-own-paths
tier: 2
impact: patch
stage: shipped
created: 2026-11-20
opened: 2026-11-20T05:37Z
updated: 2026-11-20
shipped: 2026-11-20
idea: 2026-11-20-40
depends_on:
serves: [O2]
fixes: [2026-11-20-27]
---

# 198 — A landing stages only the paths its change owns

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Bug 2026-11-20-27, found by the review of 197: "`_stray()` lets through any entry whose worktree
column is blank, so it can't tell a fully staged edit or deletion by the resolver from one the
replayed commit made. The resolver has `Bash`, and only its prompt says 'reads only'. It could
`git add` an edit to any file, or `git rm` a file only `HEAD` holds, and `--continue` would stage
it into the rebased commit, which then lands on the base." 197's `staged_gone` check closes only
the deletion case, and only for files `REBASE_HEAD` still holds.

It is the fifth escape of one class this window: 097, 104, 139 (bug 2026-11-20-14) and 196 (bug
2026-11-20-23) each read the index or a rebase's state after an earlier step had already changed
it. The escape rate rose from 0.02 to 0.20 per change. Seed 2026-11-20-40 proposes the review
doc's bullet for the class. Nit 2026-11-20-28: `staged_gone` calls `git cat-file` once per staged
deletion where one read of `REBASE_HEAD`'s tree would do.

## Outcome

- `resolve --continue` refuses any staged path that isn't one of `REBASE_HEAD`'s own paths, a
  conflicted file, a moved file or a record file, whether it was edited, added or deleted, and
  staged or not. A test drives a resolver that stages an edit outside its files and one that
  `git rm`s a file only `HEAD` holds, and sees both refused.
- `.sdlc/REVIEW.md`'s Pass 1 holds the bullet *Git state read after the step that changed it*, as
  seed 2026-11-20-40 words it.
- **Moves O2:** no change lands a file its own work and its conflict didn't touch.

## Affected

- `plugins/factory/scripts/landing.py` (`cmd_resolve --continue`, `_stray()`, `staged_gone`),
  `plugins/factory/scripts/factory.py` (`deleted_sides()` if the check moves),
  `.sdlc/REVIEW.md`, `tests/test_train.py`.
- **What reads it:** every landing train's resolve step, and every factory and ship review that
  reads the review doc. `landing.py` is in `[review] sensitive`, so the review runs at full depth.

## Constraints

- Never resolve a conflict but through the resolver or the person. This change only narrows what
  `--continue` accepts.
- A real modify/delete resolution and a moved file (196, 197) still continue.
- `.sdlc/REVIEW.md` holds only this repo's answers to `guide/review.md`
  (`tests/test_defaults.py`).
- Windows: every path is compared as `as_posix()`.

## Open questions

- ~~Should the owned-paths guard live in one function that `land`'s commit uses too, or only in
  `--continue`?~~ Resolved: only in `--continue`; `land` has no rebase under way, and
  `_amend_record()` already fences its amend (spec, Alternatives rejected).
- ~~Does a resolver ever need to stage a path `REBASE_HEAD` doesn't touch: `.sdlc/last-id`, a
  change's own records?~~ Resolved: no; the counter is staged only when it conflicted, and the
  records and DU's moved files are allowed by name (spec, Design).
