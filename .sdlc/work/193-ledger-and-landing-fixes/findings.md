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

## F1. [nit] [correctness] `by_alts` is built from every ledger entry with options.

plugins/factory/scripts/factory.py:2018: `by_alts` is built from every ledger entry with options. The match relies on options and why being identical, so a very short shared option list could merge two real decisions. D1 already accepts this trade-off.

Evidence: plugins/factory/scripts/factory.py:2018
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F2. [pre-existing] [contract] the grep refusals cover GNU grep and BSD grep only.

plugins/factory/scripts/landing.py:795: the grep refusals cover GNU grep and BSD grep only. If a host's `grep` on `PATH` is ugrep, `grep -r --dereference-files keep .` is allowed and follows links to files outside the checkout. This change didn't add or touch that gap, but it is in the same function. Fix: refuse `--dereference-files` and its prefixes too, or check every word against a list of such long options.

Evidence: plugins/factory/scripts/landing.py:795
Class: security review, round 1
Disposition: recorded
By: security

## F3. [nit] [contract] the threshold `len(name) >= 5` counts the leading `--`, while the comment above `GREP_FOLLOWS_LONG` says "three or more characters after its `--`".

plugins/factory/scripts/landing.py:883: the threshold `len(name) >= 5` counts the leading `--`, while the comment above `GREP_FOLLOWS_LONG` says "three or more characters after its `--`". Writing it as `len(name) - 2 >= 3`, or naming the constant, would make the two read the same.

Evidence: plugins/factory/scripts/landing.py:883
Class: security review, round 1
Disposition: recorded
Theme: style
Cost: S
Value: low
By: security

## F4. [nit] [correctness] the third test chains its cases in one body, so a failure in the first assertion hides the later cases

tests/test_factory.py:870: the third test chains its cases in one body, so a failure in the first assertion hides the later cases

Evidence: tests/test_factory.py:870
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
