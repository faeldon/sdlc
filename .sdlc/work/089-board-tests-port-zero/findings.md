# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

## F1. [nit] [cost] The routes test parses the port back out of the URL the fixture already gave it

`test_the_board_answers_three_gets_and_nothing_else` discards `served`'s third value, the bound
port, with `_`, then recovers it with `int(url.rsplit(":", 1)[1])`.

Evidence: tests/test_board.py:411, tests/test_board.py:426
Class: a value recomputed from a string instead of taken from where it was handed over; once here
Disposition: minor
Reason: two lines in a test, correct as written; not worth an inbox entry
