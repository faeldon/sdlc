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

## F1. [nit] [correctness] `plugins/factory/skills/land/SKILL.md` Step 3 and Step 4: the lines you edited run past the file's roughly 100-column wrap (the "`gates`, `ungated`, …" line and the Step 4 "When `ungated` is set…" line).

`plugins/factory/skills/land/SKILL.md` Step 3 and Step 4: the lines you edited run past the file's roughly 100-column wrap (the "`gates`, `ungated`, …" line and the Step 4 "When `ungated` is set…" line). Re-wrap them.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F2. [nit] [correctness] the `# fmt: skip` on the parametrize decorator exists only to keep the table on one line; a plain `ids=` list would format normally

tests/test_train.py:1546: the `# fmt: skip` on the parametrize decorator exists only to keep the table on one line; a plain `ids=` list would format normally

Evidence: tests/test_train.py:1546
Class: test review, round 1
Disposition: recorded
Theme: style
Cost: S
Value: low
By: test
