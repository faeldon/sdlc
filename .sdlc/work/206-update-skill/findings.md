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

Skill evals: ran, 1 of 1; run: .sdlc/reports/cases-2026-11-21-2

## F1. [nit] [correctness] `update_line` returns None when the sdlc install here is read from a folder, so a stale `sdlc-factory` install is also never mentioned.

scripts/sdlc.py:9507: `update_line` returns None when the sdlc install here is read from a folder, so a stale `sdlc-factory` install is also never mentioned. This follows D2 but is broader than it needs to be. Check the factory row separately if that matters

Evidence: scripts/sdlc.py:9507
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F2. [nit] [correctness] `update_line`'s first form ("this session runs X") also fires when the install is already updated and only the restart is missing.

scripts/sdlc.py:9546: `update_line`'s first form ("this session runs X") also fires when the install is already updated and only the restart is missing. `/sdlc:update` then handles it through `restart_first`, so this is fine. A short comment would say so

Evidence: scripts/sdlc.py:9546
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F3. [nit] [correctness] the fake `claude` opens its log and rows files without an encoding, unlike the `encoding="utf-8"` the repo's tests use elsewhere.

tests/test_update.py:107: the fake `claude` opens its log and rows files without an encoding, unlike the `encoding="utf-8"` the repo's tests use elsewhere. It is not a portable test, so it only matters on a non-UTF-8 locale.

Evidence: tests/test_update.py:107
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F4. [nit] [correctness] the fake `claude` opens its log and rows files without `encoding="utf-8"`.

tests/test_update.py:107: the fake `claude` opens its log and rows files without `encoding="utf-8"`. It is not a portable test, so it only matters on a non-UTF-8 locale.

Evidence: tests/test_update.py:107
Class: test review, round 2
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F5. [nit] [correctness] the fake `claude` opens its log and rows files without `encoding="utf-8"`.

tests/test_update.py:107: the fake `claude` opens its log and rows files without `encoding="utf-8"`. This is carried over from round 2 and only matters on a non-UTF-8 locale, since the test isn't portable.

Evidence: tests/test_update.py:107
Class: test review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: test
