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

Skill evals: ran, 2 of 3; environment: ship-behaviour; run: .sdlc/reports/cases-2026-11-22-2

## F1. [important] [context] It says `sdlc.py ship` "refuses a diff this applies to whose note says neither" `Docs review:` line.

skills/ship/docs.md:28: It says `sdlc.py ship` "refuses a diff this applies to whose note says neither" `Docs review:` line. `cmd_ship` now asks for that line only when `findings.md` exists (`line != "docs" or found["exists"]`, sdlc.py:4187). That is the builder's departure D1, and it is still open in `decisions.md`. Reword to "refuses, when the change has a `findings.md`, a diff this applies to whose note says neither". Check `skills/ship/SKILL.md`, the ship paragraph of `docs/REFERENCE.md` and `plugins/factory/README.md` for the same unconditional claim. D1 stays open for the person, and the doc must match whichever way it is answered.

Evidence: skills/ship/docs.md:28
Class: code review, round 1
Disposition: fixed
By: code

## F2. [nit] [correctness] `docs_review` re-reads every listed doc's full text on each `_rounds_at_depth()` call, which `status` and `verdicts` may make many times.

plugins/factory/scripts/factory.py:1010: `docs_review` re-reads every listed doc's full text on each `_rounds_at_depth()` call, which `status` and `verdicts` may make many times. It is cheap now, but a docs-site `reviewed` list could make it slow. Cache per call, or short-circuit before the read loop when `changed` has a path outside `tests/` (clause e), since the read only decides which clause holds.

Evidence: plugins/factory/scripts/factory.py:1010
Class: code review, round 1
Disposition: minor
Reason: weighed low value: below the factory's filing bar
By: code

## F3. [nit] [correctness] scripts/sdlc.py:~8010: `_docs_applies` and `docs_review` duplicate clauses (a)–(e), by the spec's no-import design.

scripts/sdlc.py:~8010: `_docs_applies` and `docs_review` duplicate clauses (a)–(e), by the spec's no-import design. A test that runs both over the same fixtures would pin them in step, as the other copies are.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: fixed
Reason: not raised again by a later round of its review
By: code
