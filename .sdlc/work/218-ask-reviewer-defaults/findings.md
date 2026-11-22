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

## F1. [nit] [correctness] `tests/test_autopilot.py:~984`: the assertion's backslash-continued f-string needs `# fmt: skip` and is hard to read.

`tests/test_autopilot.py:~984`: the assertion's backslash-continued f-string needs `# fmt: skip` and is hard to read. Two variables, or an `in` check on each part, would be clearer.

Evidence: reviews/round-2/code.md
Class: code review, round 2
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F2. [nit] [contract] `BUILT_RE` matches a `- BUILT:` line anywhere in a builder report, including one quoted inside a code fence; skipping fenced blocks would stop a quoted line from counting as built

plugins/factory/scripts/factory.py:2296: `BUILT_RE` matches a `- BUILT:` line anywhere in a builder report, including one quoted inside a code fence; skipping fenced blocks would stop a quoted line from counting as built

Evidence: plugins/factory/scripts/factory.py:2296
Class: security review, round 2
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: security

## F3. [nit] [correctness] the `cmd_ask()` docstring wraps short, leaving a line that ends at "while a".

`plugins/factory/scripts/factory.py:2282`: the `cmd_ask()` docstring wraps short, leaving a line that ends at "while a". Reflowing it would read better.

Evidence: plugins/factory/scripts/factory.py:2282
Class: test review, round 2
Disposition: recorded
Theme: style
Cost: S
Value: low
By: test
