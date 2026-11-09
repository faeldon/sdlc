# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:` and `Reason:` lines, and `By: fresh` on a
> finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings` trailer, and
> `ship` refuses while one is still `open`.

## F1. [nit] [cost] The thresholds reach print_status through a key of their own

`release_due()` already reads both thresholds, but `main()` copies them again into
`a["release_due_after"]` so `_not_due()` can say "of 5" and "of 14". Returning them in the `due`
dict would drop the extra key and its two lines in `main()`.

Evidence: scripts/sdlc.py:7590, scripts/sdlc.py:8073
Class: plumbing a value twice where the function that reads it could carry it; not seen elsewhere in status
Disposition: minor
Reason: two lines of plumbing, working and tested; fold it in whenever status's release code is next touched
