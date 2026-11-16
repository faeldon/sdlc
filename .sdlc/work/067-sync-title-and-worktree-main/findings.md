# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.
>
> Fresh review: ran
> Skill evals: ran, 1 of 1

## F1. [nit] [correctness] An intent that won't parse renames its issue to the folder name

`load_change()` returns before reading the heading when the intent's frontmatter won't parse, and
`cmd_sync` still syncs, so `issue_title` falls back to `folder.name` and the issue is renamed to
`067-sync-title-and-worktree-main`, a name `new` never gives. `sync()` already skips an empty
title, so the fallback buys nothing.

Evidence: scripts/sdlc.py:4435, scripts/sdlc.py:880, scripts/trackers/github.py:596
Class: a default given where "nothing to do" was meant; `render_issue()`'s older `rec["title"] or name` is the body's, not this diff's
Disposition: fixed
By: fresh

## F2. [nit] [contract] The config comment says `worktree_setup` runs after any `new`

Shortened to fit the line, "after `new --worktree`" became "after `new`", but the command runs
only once `new` made a worktree, the one path that prints the line `{main}` is read from.

Evidence: scripts/sdlc.py:208
Class: precision lost to fit a line; docs/REFERENCE.md:95 is right
Disposition: fixed
By: fresh

## F3. [nit] [correctness] The skill-text assertion is a test only a revert can fail

The new assertion pins a sentence in the intent skill's Step 5, which by the guide belongs in
`checks.md`.

Evidence: tests/test_skills.py:356
Class: a test only a revert can fail
Disposition: wrong
By: fresh
Reason: tests/test_skills.py is the repo's mechanism for keeping skill text and script in step (AGENTS.md, the skills' invariants), and this one fails on a later reword of Step 5 that drops `{main}` while `new` still prints the path, which is drift, not a revert
