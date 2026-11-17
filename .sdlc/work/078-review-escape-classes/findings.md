# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

## F1. [important] [correctness] The first bullet's rule is one its own cited tests break

It says a change to how an event is read "carries a test built from a real transcript's entries",
but both tests it names are built from hand-written events (`tests/test_metrics.py`'s docstring:
"Every fixture is a transcript built here under a made-up path"), and no recorded transcript
exists in `tests/`. Read as a rule, as D1 decided, the next review would hold every metrics change
to a standard nothing here meets. D1's answer: a rule, softened to the shape.

Evidence: .sdlc/REVIEW.md:45, tests/test_metrics.py:4, .sdlc/work/078-review-escape-classes/decisions.md:3
Class: a rule stated stronger than the evidence it cites
Disposition: fixed
Fix: in .sdlc/REVIEW.md's first new bullet, "a test built from a real transcript's entries" becomes "a test built from the shape of a real transcript's entries".

## F2. [nit] [correctness] The second bullet's `-z` clause names more than its test shows

059's escape was retro's hotspot paths, escaped by `git diff --numstat`, checked against a listing
that didn't escape them the same way; the test covers that pair, not `-z` as such.

Evidence: .sdlc/REVIEW.md:50, scripts/retro.py:856, tests/test_retro.py:1419
Class: a rule stated stronger than the evidence it cites
Disposition: fixed
Fix: "git's quoted path against its `-z` output" becomes "git's escaped path against an unescaped one (a `-z` listing, or another command's)".

## F3. [nit] [correctness] A cited test catches its regression only on Windows

`test_paths_shown_are_posix` passes on macOS and Linux whether or not `_shown()` calls
`as_posix()`; only CI's Windows job, which runs `tests/test_windows.py` as `portable`, would fail.

Evidence: .sdlc/REVIEW.md:51, tests/test_windows.py:310, scripts/sdlc.py:844
Class: a test cited as covering a class it only covers on one platform
Disposition: fixed
Fix: after "`test_paths_shown_are_posix` (`tests/test_windows.py`)" add ", caught only in CI's Windows job (it passes on any other platform whatever the code does),".

## F4. [nit] [correctness] The intent's two open questions are answered but not struck

Both are settled (each bullet names its tests; D1 answered the second), yet `status` still counts
them open, and the shipped intent would read as undecided.

Evidence: .sdlc/work/078-review-escape-classes/intent.md:70-74
Class: an artifact left behind its own decisions
Disposition: fixed
Fix: strike both with `~~…~~`, the first `Resolved: yes, each bullet names the tests that cover its escapes.`, the second `Resolved: a rule, softened to the shape of a real transcript's entries (D1).`
