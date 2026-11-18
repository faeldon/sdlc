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

Fresh review: skipped, the factory's rounds stand in

## F1. [nit] [correctness] `lead_time()` returns `{}` when `opened` is after `closed`, and the code files that as `lead=bad-opened`.

scripts/closing.py:474: `lead_time()` returns `{}` when `opened` is after `closed`, and the code files that as `lead=bad-opened`. That word is meant for an unparsable `opened:`. A clock that ran backwards is a different case; a distinct word such as `lead=clock` would say which one it was.

Evidence: scripts/closing.py:474
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F2. [nit] [correctness] a factory change with no timed rows and no transcript events gets `ready=None`, so `ready_wait` is dropped (`source=git`).

scripts/closing.py:431: a factory change with no timed rows and no transcript events gets `ready=None`, so `ready_wait` is dropped (`source=git`). R10's "no transcripts" case says `lead`, `ready_wait` and `landing` are kept. The code is reasonable, because there is no approver row to read `ready` from. The spec could say so, or `ready` could fall back to the tip's author date for a factory change too.

Evidence: scripts/closing.py:431
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F3. [nit] [contract] the broad `except Exception` also hides programming errors as `lead=failed`.

scripts/closing.py:475: the broad `except Exception` also hides programming errors as `lead=failed`. That fits "never refuses", but it could log the exception's type name to stderr so a regression is visible

Evidence: scripts/closing.py:475
Class: security review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: security

## F4. [nit] [correctness] the `lead=bad-opened` path for `opened` after `closed` (decision D3) has no test of its own; only a malformed value is parametrized

tests/test_archive.py: the `lead=bad-opened` path for `opened` after `closed` (decision D3) has no test of its own; only a malformed value is parametrized

Evidence: tests/test_archive.py
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
