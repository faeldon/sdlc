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

Skill evals: ran, 2 of 2; run: .sdlc/reports/cases-2026-11-21-3

## F1. [nit] [correctness] the reflowed *Setup* paragraph leaves a short line, "same change.

AGENTS.md:218: the reflowed *Setup* paragraph leaves a short line, "same change. `git.attribution` has no default on", that could be rewrapped.

Evidence: AGENTS.md:218
Class: code review, round 1
Disposition: recorded
Theme: style
Cost: S
Value: low
By: code

## F2. [nit] [correctness] the R5 test never forces a `ValueError`, so half of the `except (OSError, ValueError)` is unpinned; a second mock that raises `UnicodeDecodeError` would close it

tests/test_setup_lifecycle.py:735: the R5 test never forces a `ValueError`, so half of the `except (OSError, ValueError)` is unpinned; a second mock that raises `UnicodeDecodeError` would close it

Evidence: tests/test_setup_lifecycle.py:735
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
