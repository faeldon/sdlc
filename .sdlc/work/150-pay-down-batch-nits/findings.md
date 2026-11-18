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

Skill evals: ran, 2 of 3 (cases-2026-11-18-15)

## F1. [nit] [correctness] `_terms()` accepts a term that matches the empty string, such as `a*`, and `re.sub` then inserts `<term>` between every character.

`plugins/factory/scripts/factory.py:3050`: `_terms()` accepts a term that matches the empty string, such as `a*`, and `re.sub` then inserts `<term>` between every character. `test_nothing_local` takes the same lines, so it fails on them too. Skipping a term that matches `""` would be cheap hardening.

Evidence: plugins/factory/scripts/factory.py:3050
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F2. [important] [correctness] The ship-behaviour case failed its reads-behaviour grader

The skills' cases in scope ran 2 of 3: ship-behaviour scored 0.9, its `reads-behaviour` grader
failing ("Read called 0x"), in the run 150's cases last made.

Evidence: .sdlc/reports/cases-2026-11-18-15, case ship-behaviour
Class: a skill doing what its text forbids
Disposition: wrong
Reason: ship read behaviour.md with cat, not the Read tool, and ran the behaviour check correctly; the other failures were git failing in the eval sandbox (xcrun_db), see 156-cases-that-tell
