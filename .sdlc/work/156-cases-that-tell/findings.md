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

Skill evals: ran, 2 of 3; environment: ship-behaviour; run: .sdlc/reports/cases-2026-11-18-17

## F1. [nit] [correctness] `ceiling = int((5 - spent) * 100) / 100` can lose a cent to float error (for example 4.35 becomes 4.34).

scripts/sdlc.py:3877: `ceiling = int((5 - spent) * 100) / 100` can lose a cent to float error (for example 4.35 becomes 4.34). That is harmless, because it only errs low. Using `Decimal`, or `math.floor(x * 100 + 1e-9)`, would be more exact.

Evidence: scripts/sdlc.py:3877
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F2. [nit] [correctness] plugins/factory/skills/land/SKILL.md:~103: the decline path runs `--skip "declined at landing"`, so the note never carries the person's own reason.

plugins/factory/skills/land/SKILL.md:~103: the decline path runs `--skip "declined at landing"`, so the note never carries the person's own reason. This is the builder's D1 default, and the spec's R16 says "their reason". It matches the repo's rule that a person's words stay off command lines, and it is an open default the person can overrule.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F3. [nit] [correctness] the workspace test chmods to 0 and then restores in `finally`.

tests/test_evals.py:523: the workspace test chmods to 0 and then restores in `finally`. A failure partway through could leave `outside` unreadable for pytest's tmp cleanup.

Evidence: tests/test_evals.py:523
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
