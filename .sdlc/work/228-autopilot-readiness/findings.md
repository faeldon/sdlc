# Findings

> What a change's review found, one `## ` section a finding, committed with the change.
> `/sdlc:ship` writes it after every review, and the factory's `carry`, and its landing's rounds,
> write their agents' findings into it; `By:` names who raised one: `fresh` for ship's
> fresh-context reviewer, a factory role (`code`, `test`, …) for an agent, and no line on ship's
> own. A rerun keeps each id, marks one the diff no longer shows `fixed`, and never raises again
> one the person answered `wrong`, `intentional` or `minor`; an agent's `wrong` is its arbiter's,
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

## F1. [nit] [correctness] the reflowed sentence leaves one line well past the 100-column wrap the rest of the paragraph keeps ("outside a code fence), which answering would land unbuilt; a `verdicts` stop; one `land-check` excludes or the train").

plugins/factory/README.md:606: the reflowed sentence leaves one line well past the 100-column wrap the rest of the paragraph keeps ("outside a code fence), which answering would land unbuilt; a `verdicts` stop; one `land-check` excludes or the train"). Re-wrap it.

Evidence: plugins/factory/README.md:606
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F2. [nit] [correctness] the end-to-end test names its assertions on `"→ decided by autopilot: keep it"`.

tests/test_autopilot.py:1576: the end-to-end test names its assertions on `"→ decided by autopilot: keep it"`. That text depends on the stand-in builder's blocking line, so a change to `BUILDER_RAISES` would break it at a distance. Reference a shared constant instead.

Evidence: tests/test_autopilot.py:1576
Class: code review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: code

## F3. [nit] [correctness] the refused-agent test only exercises a resumed task, so "the sessions file is as it was" holds trivially; seed a fresh task with no sessions file and assert it is not created {tests S S med}

tests/test_land.py:2780: the refused-agent test only exercises a resumed task, so "the sessions file is as it was" holds trivially; seed a fresh task with no sessions file and assert it is not created {tests S S med}

Evidence: tests/test_land.py:2780
Class: test review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: test
