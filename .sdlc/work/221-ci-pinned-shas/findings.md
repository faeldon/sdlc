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

## F1. [nit] [correctness] `USES` only matches `uses:` at the start of a line or after `- `, so a quoted value (`uses: "a/b@v4"`) would slip through unchecked

tests/test_ci.py:15: `USES` only matches `uses:` at the start of a line or after `- `, so a quoted value (`uses: "a/b@v4"`) would slip through unchecked

Evidence: tests/test_ci.py:15
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F2. [nit] [contract] the workflow glob misses `.github/workflows/*.yaml`, which GitHub also runs, so an unpinned action there would pass the test; glob both extensions

tests/test_ci.py:52: the workflow glob misses `.github/workflows/*.yaml`, which GitHub also runs, so an unpinned action there would pass the test; glob both extensions

Evidence: tests/test_ci.py:52
Class: security review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: med
By: security

## F3. [nit] [correctness] `VERSION` demands a `v` plus digits, so a comment like `# release-2` would be refused; that is stricter than the outcome's wording but matches the plan

tests/test_ci.py:16: `VERSION` demands a `v` plus digits, so a comment like `# release-2` would be refused; that is stricter than the outcome's wording but matches the plan

Evidence: tests/test_ci.py:16
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F4. [nit] [correctness] `USES` still misses a quoted `uses: "a/b@v4"`

tests/test_ci.py:15: `USES` still misses a quoted `uses: "a/b@v4"`

Evidence: tests/test_ci.py:15
Class: code review, round 2
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F5. [nit] [correctness] `VERSION` demands `v` plus digits, so a comment like `# release-2` is refused; this is stricter than the outcome's wording but matches the plan

tests/test_ci.py:16: `VERSION` demands `v` plus digits, so a comment like `# release-2` is refused; this is stricter than the outcome's wording but matches the plan

Evidence: tests/test_ci.py:16
Class: test review, round 2
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
