# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:` and `Reason:` lines, and `By: fresh` on a
> finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings` trailer, and
> `ship` refuses while one is still `open`.

## F1. [nit] [correctness] A hotspot's `lines: null` reads as deleted for a binary or empty file

`hotspots()` takes `lines` from `git grep -I -c ''`, which leaves out binary and empty files, so a
much-edited image or an empty `__init__.py` shows `lines: null`, which its docstring and the spec
call "once it is gone". The retrospective could read a live file as deleted.

Evidence: scripts/indicators.py:157 (`now.get(p)`), scripts/sdlc.py `_line_counts()`
Class: a null carrying two meanings; not elsewhere in this diff
Disposition: recorded

## F2. [nit] [cost] The look-back recomputes the window's changes' numstat

`_architecture()` runs `_change_rows()` for each of the last 30 changes, and the window's changes
among them were already diffed in `retro()`'s loop: a handful of repeated `_change_base` and
`git diff` calls per retrospective.

Evidence: scripts/sdlc.py `_architecture()` (`lookback = [_change_rows(home, rec)[1] ...]`)
Class: repeated git walk; status's double walk (2026-10-25-15) is the same kind
Disposition: minor
Reason: about seven extra git calls once per retrospective, which runs after a couple of releases
