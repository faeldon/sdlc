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
>
> The sdlc:reviewer agent returned F1–F4; each was confirmed by reading the code it cites.

## F1. [important] [correctness] A present non-ASCII hotspot reads `gone: true`

The hotspot paths come from `git diff --numstat` and `diff-tree --numstat` with the default
`core.quotePath`, so `café.py` arrives quoted; the new `ls-tree` listing passes
`core.quotePath=false`, so `present` holds it unquoted, and `p not in present` calls a file still
on the base branch deleted. notes.md's departure claiming the flag matches the other listings is
wrong: those are compared with each other, not with numstat.

Evidence: scripts/sdlc.py:6376 against scripts/sdlc.py:6336, scripts/sdlc.py:6338; scripts/indicators.py:168
Class: two git outputs with different path quoting compared as strings
Disposition: fixed
By: fresh

## F2. [nit] [correctness] R8's skip rule is pinned only in part

The one test covers a marked issue skipped and one with a parent viewed; nothing fails if the
`close` or `needs_info` guard is removed, and the first run's view of an unmarked issue isn't
asserted.

Evidence: scripts/sdlc.py:7356, tests/test_archive.py:1707
Class: a requirement whose conditions have code but no failing test
Disposition: fixed
By: fresh

## F3. [nit] [cost] `sync` lists every open issue's comments to mark one or two

`sync` calls `mark_issues(..., only=closes)` on each intent, spec and ship run; the new listing
pulls every open issue's comments (limit 1000) where a numbers listing and one or two views did,
and a failed heavy listing marks nothing rather than falling back to `open_numbers`.

Evidence: scripts/sdlc.py:2208, scripts/sdlc.py:7342, scripts/trackers/github.py:320
Class: a batch read replacing per-item reads even for one or two items
Disposition: fixed
By: fresh

## F4. [nit] [correctness] `mark_issues` can now raise before its try

`getattr(found, "open_marks", None) or found.open_numbers` runs before the `try`, so a tracker
lacking `open_numbers` raises from a function documented "Never raises".

Evidence: scripts/sdlc.py:7333, scripts/sdlc.py:7342
Class: work moved outside the guard that kept a function from raising
Disposition: fixed
By: fresh

## F5. [nit] [correctness] A failed path listing calls every hotspot gone

`_git` returns None when `ls-tree` fails, which becomes an empty `present`, so every hotspot reads
`gone: true` instead of unknown.

Evidence: scripts/sdlc.py:6377
Class: a failed read taken as an empty answer
Disposition: fixed
