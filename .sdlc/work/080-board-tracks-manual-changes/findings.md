# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

## F1. [nit] [cost] Each poll runs `git status` twice in a change's worktree

`_seen()` calls `_dirty_paths()` on the checkout `last_touched()` has just run the same status in,
so every two-second poll lists each worktree's changes twice.

Evidence: scripts/board.py:161 (`_dirty_paths(checkout)`), scripts/sdlc.py:3267 (`last_touched()`'s own)
Class: a reader repeated where one result could be shared; nowhere else in the board
Disposition: minor
Reason: one extra `git status` per open worktree every two seconds, on a board a person starts by
hand and watches a handful of changes on; sharing it means changing `last_touched()`'s signature,
which `status` calls too, for no visible gain
