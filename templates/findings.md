# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

## F1. [<important|nit|pre-existing>] [<correctness|contract|cost|context>] <what's wrong>

<What's wrong and what it breaks, in a sentence or two.>

Evidence: <path:line, read, never guessed from a name>
Class: <the kind of mistake, and whether it appears elsewhere>
Disposition: <open|fix|fixed|recorded|wrong|intentional|minor>
Fix: <the exact change, for fix; otherwise delete this line>
Reason: <why, for wrong, intentional or minor; otherwise delete this line>
