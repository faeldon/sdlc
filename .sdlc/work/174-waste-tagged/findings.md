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

## F1. [nit] [correctness] `_cost()` runs once in `retro()` and again in `retro_report()`, and each run re-reads every change's commit.

scripts/retro.py:1752: `_cost()` runs once in `retro()` and again in `retro_report()`, and each run re-reads every change's commit. Computing it once per `retro` call would halve the git reads.

Evidence: scripts/retro.py:1752
Class: code review, round 1
Disposition: recorded
Theme: refactor
Cost: M
Value: low
By: code

## F2. [nit] [correctness] if `claude` returns no figures, no row is written, so a run that failed that way doesn't make the next try a `rerun`.

plugins/factory/scripts/factory.py:4392: if `claude` returns no figures, no row is written, so a run that failed that way doesn't make the next try a `rerun`. This matches R3 as worded. A line in the `purpose_of()` docstring would say so.

Evidence: plugins/factory/scripts/factory.py:4392
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F3. [nit] [correctness] R1's `land` field is never asserted on a row written by `cmd_agent` for a landing task.

tests/test_factory.py: R1's `land` field is never asserted on a row written by `cmd_agent` for a landing task. `purpose_of` is tested for it, but no test runs a `land-review` through `cmd_agent` and checks the row carries `land`.

Evidence: tests/test_factory.py
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F4. [nit] [correctness] the stop half of `test_an_ejection_is_recorded_and_amended_in` doesn't check `at` or `land` on its rows.

tests/test_train.py: the stop half of `test_an_ejection_is_recorded_and_amended_in` doesn't check `at` or `land` on its rows. Only `cause` is asserted.

Evidence: tests/test_train.py
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
