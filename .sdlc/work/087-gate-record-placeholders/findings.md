# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

## F1. [nit] [correctness] A path that only starts with the home directory's is partly replaced

`_placeholders()` replaces the home directory as a plain substring, so a path that merely shares
its prefix (home `/home/ana`, output naming `/home/anabel/…`) is written `~bel/…`, and the same
goes for a sibling of the checkout (`<path-to-clone>-old/…`). The record stays free of the
machine's path; it only reads oddly.

Evidence: plugins/factory/scripts/factory.py:1266
Class: substring replacement where a path-boundary match was meant; no other replacement of this kind in factory.py
Disposition: minor
Reason: needs another user's home or a sibling checkout named in the gate's output, and even then hides the path; a boundary-aware match isn't worth its regex
