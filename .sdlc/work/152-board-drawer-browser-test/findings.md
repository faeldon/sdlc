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

## F1. [nit] [correctness] the header comment line now runs to 166 characters; the rest of the file wraps near 100.

.github/workflows/check.yml:3: the header comment line now runs to 166 characters; the rest of the file wraps near 100. Re-wrap it

Evidence: .github/workflows/check.yml:3
Class: code review, round 1
Disposition: recorded
Theme: style
Cost: S
Value: low
By: code

## F2. [nit] [correctness] the intent's open question on a skip note in `./check.sh`'s summary is not addressed.

tests/test_board_browser.py:75: the intent's open question on a skip note in `./check.sh`'s summary is not addressed. Recorded here as a possible follow-up; the gate record shows 28 skipped without saying why

Evidence: tests/test_board_browser.py:75
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F3. [pre-existing] [contract] no `permissions:` block; set `permissions: contents: read` so a compromised dev dependency running in CI can't use a write-scoped token

.github/workflows/check.yml:13: no `permissions:` block; set `permissions: contents: read` so a compromised dev dependency running in CI can't use a write-scoped token

Evidence: .github/workflows/check.yml:13
Class: security review, round 1
Disposition: recorded
By: security

## F4. [nit] [contract] the rewrapped header comment runs past the file's line width

.github/workflows/check.yml:3: the rewrapped header comment runs past the file's line width

Evidence: .github/workflows/check.yml:3
Class: security review, round 1
Disposition: recorded
Theme: style
Cost: S
Value: low
By: security

## F5. [nit] [correctness] the reflowed header comment leaves one line far over the file's roughly 100-column wrapping

.github/workflows/check.yml:3: the reflowed header comment leaves one line far over the file's roughly 100-column wrapping

Evidence: .github/workflows/check.yml:3
Class: test review, round 1
Disposition: recorded
Theme: style
Cost: S
Value: low
By: test

## F6. [nit] [correctness] the test takes about 49s here, mostly waiting on the poll interval.

tests/test_board_browser.py:98: the test takes about 49s here, mostly waiting on the poll interval. A shorter bounded wait or a faster poll in the fixture would speed up `./check.sh`

Evidence: tests/test_board_browser.py:98
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: M
Value: low
By: test
