# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

Fresh review: ran

## F1. [pre-existing] [correctness] Close's `reaches` says nothing of a change to `.claude/settings.json`

`enabledPlugins` is read when a session starts, so this change asks every open session in the repo
for `/reload-plugins` or a restart. `landing_reach()` classifies no `.claude/` path, so `_reaches()`
returns None and close reports that the landed change asks nothing of anyone.

Evidence: scripts/sdlc.py:4355-4369 (no branch for `.claude/`), scripts/sdlc.py:4388 (`or None`)
Class: a reach table missing a path kind; the lines predate this diff, which only meets them
Disposition: recorded
By: fresh
