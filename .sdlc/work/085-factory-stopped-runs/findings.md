# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

## F1. [nit] [correctness] The board's stop reader isn't guarded, so an unreadable record breaks the whole page

`_stopped()` calls `read_text` outside `_entry()`'s `read()` guard, so a `runs/stopped.md` that
can't be opened (a directory there, no permission) raises out of `/state.json` instead of becoming
a `problems` line, as R7 and every other file read in `_entry()` do. `sdlc.py`'s `factory_stop()`
already catches `OSError`. The code reviewer and the approver raised it too.

Evidence: scripts/board.py:135, scripts/board.py:241
Class: a file read outside the reader's own error guard; the rest of `_entry()` is guarded
Disposition: fixed

## F2. [nit] [context] The intent's last open question is still unstruck

`/sdlc:status` counts it ("1 open question(s)"), and a shipped folder isn't read again. 084 landed
and 078 has since closed (`260a75e`) with nothing from this change, so the question is answered:
078 needed nothing, and the live case became the board test built from its round-1 files.

Evidence: .sdlc/work/085-factory-stopped-runs/intent.md:94
Class: an artifact left unsettled at ship
Disposition: fixed
