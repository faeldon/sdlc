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

Fresh review: skipped, the factory's rounds stand in

## F1. [nit] [correctness] a read that printed output and then hits a blank line and a `## Notes` heading with no `exit:` keeps the section open.

plugins/factory/scripts/factory.py:1586: a read that printed output and then hits a blank line and a `## Notes` heading with no `exit:` keeps the section open. Any later `$ ` line in that report is then counted as an evidence command. This is a deliberate trade-off and the docstring says so, but a test pinning that case would make it explicit.

Evidence: plugins/factory/scripts/factory.py:1586
Class: code review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: code

## F2. [nit] [contract] restrict the missing-file pass to `deleted_sides()` paths so a `UU` file can't silently become a staged deletion

plugins/factory/scripts/landing.py:2827: restrict the missing-file pass to `deleted_sides()` paths so a `UU` file can't silently become a staged deletion

Evidence: plugins/factory/scripts/landing.py:2827
Class: security review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: med
By: security

## F3. [nit] [contract] the docstring says a command that owes its `exit:` "never finds it in a later section", but a heading with no blank line before it doesn't end the section

plugins/factory/scripts/factory.py:1569: the docstring says a command that owes its `exit:` "never finds it in a later section", but a heading with no blank line before it doesn't end the section

Evidence: plugins/factory/scripts/factory.py:1569
Class: security review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: security

## F4. [nit] [correctness] a read whose printed heading follows a blank line (the `## Speed` line in 189's report) is only covered by the one combined case, so a regression to the blank-line rule would show up only there

tests/test_evidence_headings.py:1: a read whose printed heading follows a blank line (the `## Speed` line in 189's report) is only covered by the one combined case, so a regression to the blank-line rule would show up only there

Evidence: tests/test_evidence_headings.py:1
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
