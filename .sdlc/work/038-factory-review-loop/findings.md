# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:` and `Reason:` lines, and `By: fresh` on a
> finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings` trailer, and
> `ship` refuses while one is still `open`.
>
> Fresh review: not run: this diff touches no `[review] sensitive` path.

## F1. [important] [correctness] A change asking for a new file is flagged pre-existing

`untouched` lists every `CHANGE:` whose path isn't among the changed paths, so a request to create
one (`tests/test_new.py: add a test for R4`, the test reviewer's usual ask) is called pre-existing,
and the verifier is told to drop it: the missing test never reaches the builder. Only a path that
exists in the checkout and that the change didn't touch is pre-existing.

Evidence: plugins/factory/scripts/factory.py:637
Class: absence read as "not this change's"; the verifier's untouched rule repeats it
Disposition: fixed

## F2. [nit] [correctness] A CHANGES verdict with no CHANGE lines no longer reaches a rework

A reviewer that writes `VERDICT: CHANGES` but lists no `- CHANGE:` line now goes to `verify` with
nothing to answer, then to the approver, where before the builder reworked against the review.
Treat it as a stop, or carry the verdict to the approver as an open item.

Evidence: plugins/factory/scripts/factory.py:658
Class: a malformed reply passed on rather than refused; none other in the diff
Disposition: fixed
