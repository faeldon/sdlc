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

Skill evals: ran, 2 of 3; environment: intent; run: .sdlc/reports/cases-2026-11-19-2
Fresh review: skipped, the factory's rounds stand in

## F1. [nit] [correctness] the refusal message is long and repeats `FIX: ALREADY MADE`

plugins/factory/scripts/landing.py:1420: the refusal message is long and repeats `FIX: ALREADY MADE`

Evidence: plugins/factory/scripts/landing.py:1420
Class: code review, round 1
Disposition: recorded
Theme: style
Cost: S
Value: low
By: code

## F2. [nit] [contract] `taken_lines()` counts every indented line after a `Nits taken in:` line as part of it, so an indented sub-bullet that names an id to say it's left out would retire that nit.

plugins/factory/scripts/factory.py:4699: `taken_lines()` counts every indented line after a `Nits taken in:` line as part of it, so an indented sub-bullet that names an id to say it's left out would retire that nit. Only the change's own author can write this, and the intent asked for an explicit marker, so the risk is low. Stopping continuation at a line that starts a new `-` bullet would tighten it

Evidence: plugins/factory/scripts/factory.py:4699
Class: security review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: security

## F3. [nit] [correctness] the `_already_made` helper and `test_a_fix_commit_needs_an_ask` write `MADE` and `ALREADY` module constants in the middle of the file, and `tests/test_train.py` defines a second `MADE`; hoist them or rename them to avoid confusion

tests/test_land.py: the `_already_made` helper and `test_a_fix_commit_needs_an_ask` write `MADE` and `ALREADY` module constants in the middle of the file, and `tests/test_train.py` defines a second `MADE`; hoist them or rename them to avoid confusion

Evidence: tests/test_land.py
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
