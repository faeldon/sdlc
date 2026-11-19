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
> `Fresh review: skipped, <why>`. Each of ship's further passes that applies says the same on a
> line of its own: `Security review:`, `Behaviour check:`, `UI review:` and `UX review:`, and
> their findings' `By:` is `ship-security`, `ship-behaviour`, `ship-ui` or `ship-ux`, counted as
> ship's own (`passes=` says how many). A behaviour check that ran ends the file with an
> `## Evidence` section: each command on a `$ ` line, the tail of its output, then `exit: <n>`.

Fresh review: skipped, the factory's rounds stand in

## F1. [nit] [correctness] `check.sh`:12: the comment's wording on `skipped` is in `check.sh` only.

`check.sh`:12: the comment's wording on `skipped` is in `check.sh` only. The plan counted 28 skipped board tests, but the comment gives no number. That avoids rot and is correct as written.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F2. [nit] [correctness] the round-file sentence ("and `factory.py` writes it to `.sdlc/work/NNN-slug/reviews/round-N/test.md`…") is 105 columns, the same shape -81 fixed in `reviewer-code.md` and `reviewer-ux.md`; its "Under a decision's line" paragraph is probably the same; the change names only the first two files, so this is out of scope here

plugins/factory/agents/reviewer-test.md:13: the round-file sentence ("and `factory.py` writes it to `.sdlc/work/NNN-slug/reviews/round-N/test.md`…") is 105 columns, the same shape -81 fixed in `reviewer-code.md` and `reviewer-ux.md`; its "Under a decision's line" paragraph is probably the same; the change names only the first two files, so this is out of scope here

Evidence: plugins/factory/agents/reviewer-test.md:13
Class: test review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: test

## F3. [nit] [correctness] the first check covers only the seven named files, so a rewrap that regressed another agent file would not be caught; fine for this scope

.sdlc/work/173-style-paydown/checks.md: the first check covers only the seven named files, so a rewrap that regressed another agent file would not be caught; fine for this scope

Evidence: .sdlc/work/173-style-paydown/checks.md
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F4. [nit] [correctness] diagram and table rows run past 100 columns, which a prose re-wrap can't fix; leave them

plugins/factory/README.md:51: diagram and table rows run past 100 columns, which a prose re-wrap can't fix; leave them

Evidence: plugins/factory/README.md:51
Class: code review, landing round 3
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code
