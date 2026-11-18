# Findings

> What a change's review found, one `## ` section a finding, committed with the change.
> `/sdlc:ship` writes it after every review, and the factory's `carry` writes its agents' findings
> into it; `By:` names who raised one: `fresh` for ship's fresh-context reviewer, a factory role
> (`code`, `test`, …) for an agent, and no line on ship's own. A rerun keeps each id, marks one the
> diff no longer shows `fixed`, and never raises again one the person answered `wrong`,
> `intentional` or `minor`; an agent's `wrong` is its verifier's, never the person's, and the same
> fault worded differently is one more. `sdlc.py` reads each heading and its `Evidence:`, `Class:`,
> `Disposition:`, `Reason:`, `By:` and `Fix:` lines, counts ship's own alone into the
> `Sdlc-Findings` trailer (its `agents=` says how many it left out), words ship's question from
> the ones proposed `fix`, and `ship` refuses while one is still `open` or `fix`. On a diff that
> touches a sensitive path, this note also says `Fresh review: ran`, or `Fresh review: skipped,
> <why>`.

## F1. [nit] [correctness] this line still describes `exhausted` only as "rounds ran out".

plugins/factory/skills/build/SKILL.md:416: this line still describes `exhausted` only as "rounds ran out". It is now also true for a `stuck` or `untestable` stop. Add a clause saying the approver is told which.

Evidence: plugins/factory/skills/build/SKILL.md:416
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: med
By: code

## F2. [nit] [correctness] its diff is 5 lines, against 8 for the other reviewers.

plugins/factory/agents/reviewer-ux.md: its diff is 5 lines, against 8 for the other reviewers. Check that the word-for-word re-raise sentence reads the same there.

Evidence: plugins/factory/agents/reviewer-ux.md
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F3. [nit] [correctness] R6's README table of changes 124, 125, 129 and 131 has no test.

tests/test_factory.py:1676: R6's README table of changes 124, 125, 129 and 131 has no test. It cannot be checked mechanically, so a person should confirm it against each change's `Close` commit.

Evidence: tests/test_factory.py:1676
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F4. [nit] [correctness] the R3 test has no case where round N-1 has no `verified.md`, which the code handles.

tests/test_factory.py:1358: the R3 test has no case where round N-1 has no `verified.md`, which the code handles. A one-line fixture would pin that branch.

Evidence: tests/test_factory.py:1358
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
