# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

## F1. [nit] [correctness] The spec's R3 still says byte for byte, but one field changes

R3 promises that `retro` and `retro --metrics` print byte for byte what the base printed. The move
changes `prose.sdlc_py_lines` from 9,481 to 8,328 on purpose: the field counts `sdlc.py`, which
shrank. `notes.md` and `checks.md` both say so, but `spec.md`, which the review checks against,
still states the stricter promise.

Evidence: .sdlc/work/068-retro-module/spec.md:33 (R3); scripts/retro.py:97 (`script = sdlc.PLUGIN_DIR / "scripts" / "sdlc.py"`); checks.md's `jq -S 'del(.prose.sdlc_py_lines)'`
Class: a requirement narrowed while building, with the spec left as written; not seen elsewhere in this diff
Disposition: fixed

## F2. [nit] [context] Two lines of AGENTS.md's Retrospectives paragraph run past 100 characters

After the new opening sentences were added, the rewrap left two lines at 105 and 118 characters,
where the rest of the doc wraps at 100.

Evidence: AGENTS.md:185-186 ("argument in `retro.py` can't read `sdlc`, …" and "bounded by the newest `Retrospective YYYY-MM-DD` commit, …")
Class: a doc edited in place without rewrapping the lines after it; not seen elsewhere in this diff
Disposition: fixed
