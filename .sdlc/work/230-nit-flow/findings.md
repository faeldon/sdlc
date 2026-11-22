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

Skill evals: ran, 1 of 1; run: .sdlc/reports/cases-2026-11-22-1

## F1. [nit] [correctness] `again` runs `_nit_path` over every later nit once for each earlier nit, so the work grows as nits × rounds × nits.

plugins/factory/scripts/factory.py:3013: `again` runs `_nit_path` over every later nit once for each earlier nit, so the work grows as nits × rounds × nits. The sets are tiny, so computing each later round's path set once per role would be tidier than urgent.

Evidence: plugins/factory/scripts/factory.py:3013
Class: code review, round 1
Disposition: recorded
Theme: refactor
Cost: S
Value: low
By: code

## F2. [nit] [correctness] the `kind != "nit" and (by or is_building(e))` branch is correct.

scripts/sdlc.py:7776: the `kind != "nit" and (by or is_building(e))` branch is correct. A short comment would help, saying that a nit's claim check is deliberately separate from `_claimed_by`.

Evidence: scripts/sdlc.py:7776
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F3. [nit] [correctness] the test sets `start` on a round by hand to model a restart.

tests/test_factory_loop.py:921: the test sets `start` on a round by hand to model a restart. A restart that went through `cmd_restart` is exercised only in the R4 prompt test, not for filing.

Evidence: tests/test_factory_loop.py:921
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
