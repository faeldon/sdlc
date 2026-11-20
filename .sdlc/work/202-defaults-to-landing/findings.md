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

Skill evals: ran, 2 of 3; environment: ship; run: .sdlc/reports/cases-2026-11-20-2
Fresh review: skipped, the factory's rounds stand in

## F1. [nit] [correctness] `uncarried()` reports `named` (an id in both SETTLED and CONFIRM) only when the id is also CONFIRMed.

plugins/factory/scripts/run_state.py:104: `uncarried()` reports `named` (an id in both SETTLED and CONFIRM) only when the id is also CONFIRMed. A default that is open and listed as SETTLED but not ticked, because `decisions` was skipped or refused it, reads as "no `- CONFIRM:` line". The mend text then points the approver at the wrong fix. Naming the SETTLED line in that case would be clearer.

Evidence: plugins/factory/scripts/run_state.py:104
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F2. [nit] [contract] `intent_closes()` reads `closes:` from the branch's own intent.md while the sensitive bar is read from the base branch; read it from the fork point so a build can't widen what it may carry

plugins/factory/scripts/factory.py:1973: `intent_closes()` reads `closes:` from the branch's own intent.md while the sensitive bar is read from the base branch; read it from the fork point so a build can't widen what it may carry

Evidence: plugins/factory/scripts/factory.py:1973
Class: security review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: security

## F3. [nit] [correctness] the "closes" case writes `closes: [12]` by string-replacing `idea:` in `intent.md`.

tests/test_factory_decisions.py:523: the "closes" case writes `closes: [12]` by string-replacing `idea:` in `intent.md`. If the fixture's frontmatter changes, the case could pass without exercising the `closes:` rule, though the assertion on `closes: [12]` in the problem text would still catch that.

Evidence: tests/test_factory_decisions.py:523
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
