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

## F1. [nit] [correctness] the "Modules loaded by path" and "The board" edits leave lines far over the file's wrap width (about 100 columns)

AGENTS.md:68: the "Modules loaded by path" and "The board" edits leave lines far over the file's wrap width (about 100 columns)

Evidence: AGENTS.md:68
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F2. [nit] [correctness] the `FACTORY_LAND_STOPS == board.LAND_STOPS` pin is dropped, which the plan records and which is reasonable.

tests/test_board.py: the `FACTORY_LAND_STOPS == board.LAND_STOPS` pin is dropped, which the plan records and which is reasonable. It was a comparison of two copies, and with one copy it would compare the module with itself. `LAND_STOPS` still has no factory twin, so nothing checks it against the factory. It is only pinned against `LAND_STEPS` through the board's `LAND_AT` test.

Evidence: tests/test_board.py
Class: code review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: code

## F3. [nit] [correctness] a few helper names such as `_reached` and `_named` have no docstring

tests/test_modules.py: a few helper names such as `_reached` and `_named` have no docstring

Evidence: tests/test_modules.py
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F4. [nit] [correctness] `_lead_marks` reaches `factory_records` as `records` in one branch and as `sdlc.factory_records` in the other.

`scripts/closing.py:326`: `_lead_marks` reaches `factory_records` as `records` in one branch and as `sdlc.factory_records` in the other. Using the local alias in both would read more evenly.

Evidence: scripts/closing.py:326
Class: code review, landing round 2
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code
