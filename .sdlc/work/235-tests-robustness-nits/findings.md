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

## F1. [nit] [correctness] the reflowed Step 1 line is now well past the file's wrapping width

plugins/factory/skills/autopilot/SKILL.md:99: the reflowed Step 1 line is now well past the file's wrapping width

Evidence: plugins/factory/skills/autopilot/SKILL.md:99
Class: test review, round 1
Disposition: minor
Reason: weighed low value: below the factory's filing bar
By: test

## F2. [nit] [context] the new quoting sentence runs past the wrapped width and breaks the file's line wrapping

plugins/factory/skills/autopilot/SKILL.md:99: the new quoting sentence runs past the wrapped width and breaks the file's line wrapping

Evidence: plugins/factory/skills/autopilot/SKILL.md:99
Class: docs review, round 1
Disposition: minor
Reason: weighed low value: below the factory's filing bar
By: docs
