# Findings

> What a change's review found, one `## ` section a finding, committed with the change.
> `/sdlc:ship` writes it after every review, and the factory's `carry`, and its landing's rounds,
> write their agents' findings into it; `By:` names who raised one: `fresh` for ship's
> fresh-context reviewer, a factory role (`code`, `test`, …) for an agent, and no line on ship's
> own. A rerun keeps each id, marks one the diff no longer shows `fixed`, and never raises again
> one the person answered `wrong`, `intentional` or `minor`; an agent's `wrong` is its verifier's,
> never the person's, and the same fault worded differently is one more. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:`, `By:` and `Fix:` lines, counts
> ship's own alone into the `Sdlc-Findings` trailer (its `agents=` says how many it left out),
> words ship's question from the ones proposed `fix`, and `ship` refuses while one is still `open`
> or `fix`. On a diff that touches a sensitive path, this note also says `Fresh review: ran`, or
> `Fresh review: skipped, <why>`.

## F1. [nit] [correctness] `stop_text` types `stuck` and `untestable` as `list[str] = ()`.

plugins/factory/scripts/factory.py:1956: `stop_text` types `stuck` and `untestable` as `list[str] = ()`. The annotation says list while the default is a tuple. `list[str] | tuple = ()` or `None` would match what callers pass.

Evidence: plugins/factory/scripts/factory.py:1956
Class: code review, round 1
Disposition: recorded
Theme: style
Cost: S
Value: low
By: code

## F2. [nit] [correctness] `status`'s `needs_of` call for ready (shipped) changes builds a minimal `reading` dict by hand.

scripts/sdlc.py:9986: `status`'s `needs_of` call for ready (shipped) changes builds a minimal `reading` dict by hand. A test pins the resulting output, so this is fine. If `needs_of` later reads more fields at `shipped`, this site is easy to miss.

Evidence: scripts/sdlc.py:9986
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code
