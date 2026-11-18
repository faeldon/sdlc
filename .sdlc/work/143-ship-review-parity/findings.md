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
> `Fresh review: skipped, <why>`.

Skill evals: ran, 3 of 3

## F1. [nit] [correctness] the line says "whose own behaviour reviewer ran" and security.md and ui.md say the same of their factory reviewers.

skills/ship/behaviour.md:3: the line says "whose own behaviour reviewer ran" and security.md and ui.md say the same of their factory reviewers. Only the factory case is meant, so "a factory run, whose own reviewers ran" would match `_passes_report()`'s wording.

Evidence: skills/ship/behaviour.md:3
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F2. [nit] [correctness] it says the pass applies when the diff touches a `review.sensitive` path.

skills/ship/security.md:3: it says the pass applies when the diff touches a `review.sensitive` path. The script keys on `risk.deep`, so the sentence is only as exact as `deep` is. Say "a deep diff" to follow R2.

Evidence: skills/ship/security.md:3
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F3. [nit] [correctness] scripts/sdlc.py (`_passes_report`): `cmd_preflight`, `cmd_ship` and `cmd_ship_question` each call it, so `git show` and `changed_paths` run three times per ship.

scripts/sdlc.py (`_passes_report`): `cmd_preflight`, `cmd_ship` and `cmd_ship_question` each call it, so `git show` and `changed_paths` run three times per ship. That is harmless at this size, but it could be cached per run if ship slows down.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code
