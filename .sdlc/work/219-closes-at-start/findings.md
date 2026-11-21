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

## F1. [nit] [correctness] `recorded_closes()` reads the whole ledger on every call, and `record_closes()` calls it on every agent run.

plugins/factory/scripts/factory.py:3181: `recorded_closes()` reads the whole ledger on every call, and `record_closes()` calls it on every agent run. The ledger is small, so the cost is negligible.

Evidence: plugins/factory/scripts/factory.py:3181
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F2. [nit] [contract] in `cmd_agent`, `_record_land()` runs before `record_closes()`, so if the ledger append fails, the landing step is recorded for an agent that is then refused.

plugins/factory/scripts/factory.py:5095: in `cmd_agent`, `_record_land()` runs before `record_closes()`, so if the ledger append fails, the landing step is recorded for an agent that is then refused. Recording `closes:` first would make the refusal leave nothing behind.

Evidence: plugins/factory/scripts/factory.py:5095
Class: security review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: security

## F3. [pre-existing] [correctness] none found.

none found.

Evidence: reviews/round-1/behaviour.md
Class: behaviour review, round 1
Disposition: recorded
By: behaviour
