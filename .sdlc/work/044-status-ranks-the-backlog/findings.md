# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:` and `Reason:` lines, and `By: fresh` on a
> finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings` trailer, and
> `ship` refuses while one is still `open`.

## F1. [nit] [correctness] The no-theme nudge and `(no theme)` count different entries

The nudge counts ready and waiting ideas and bugs, while `Themes:` counts only ready ones, so on
this repo's register status says `32 ideas and bugs have no theme` beside `(no theme)  31`. A
person reading the two lines can't tell which is right. Cost S, value med: count waiting seeds in
`Themes:` too, since they are open entries the themes pass will reach.

Evidence: scripts/sdlc.py:5173, scripts/sdlc.py:5205
Class: two counts of one set built from different filters; none elsewhere in status
Disposition: fixed

## F2. [nit] [correctness] A change folder in the main checkout reads as in flight from any dirty file there

`last_touched()` takes every path `git status` lists in the change's checkout. For a change made
without `--worktree`, that is the main checkout, so an unrelated uncommitted edit there (an
inbox entry being drafted) marks the change touched, and the status skill never recommends it.
Every change `/sdlc:intent` opens has its own worktree, so only a hand-made folder hits it. Cost S,
value low: keep only the paths under the change's own folder when its checkout is the main one.

Evidence: scripts/sdlc.py:2773
Class: a checkout-wide signal read as one change's; none elsewhere
Disposition: recorded

## F3. [nit] [contract] The new tests aren't marked `portable`

The spec's Contracts say new tests that need no shebang fakes are marked `portable`, so CI's
Windows job runs them. None of the eight are. The code they cover (file mtimes, paths from
`git status`) is exactly what differs on Windows. Cost S, value med: mark the eight, which use only
git and the script's own functions.

Evidence: tests/test_next_up.py:328, tests/test_next_up.py:429
Class: a spec contract not carried into the tests; the rest of tests/test_next_up.py predates it
Disposition: fixed
