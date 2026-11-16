# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

## F1. [nit] [cost] The write-mode check's mode lookup reads as one wrapped slice

The formatter wrapped `c.args[1 if builtin else 0 :][:1]` across three lines, so which positional
argument is the mode, the second for `open(p, mode)` and the first for `p.open(mode)`, takes
working out.

Evidence: tests/test_windows.py:215
Class: a dense expression the formatter made harder to read
Disposition: fixed

## F2. [nit] [correctness] The md names a skill may cite are read from the disk, not from git

`_MD_NAMES` walks every `*.md` under the checkout, so an untracked local file (an ignored
`.sdlc/reports/` run, a scratch note) counts as known here and not in CI: a stale pointer can pass
locally and fail only there.

Evidence: tests/test_skills.py:766
Class: a test whose input differs between a checkout and CI
Disposition: fixed
