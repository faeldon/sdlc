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

## F1. [nit] [correctness] R5's test covers the eject path only.

tests/test_train.py: R5's test covers the eject path only. The same `problems.append(f"{name}: {problem}")` branch in `_train_stop` has no failing-append test.

Evidence: tests/test_train.py
Class: code review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: code

## F2. [nit] [correctness] scripts/retro.py `_workarounds`: when `trunk` is empty, `_log_blocks` still runs with `"..None"`-style arguments, and the result is then thrown away by `commits if trunk else []`.

scripts/retro.py `_workarounds`: when `trunk` is empty, `_log_blocks` still runs with `"..None"`-style arguments, and the result is then thrown away by `commits if trunk else []`. Guard it before the call.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F3. [nit] [correctness] scripts/retro.py `_workarounds`: `_closing_subject` is defined after its first use.

scripts/retro.py `_workarounds`: `_closing_subject` is defined after its first use. That works, but it reads out of order.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F4. [nit] [correctness] the `unknown` rows carry a `change` key that no test asserts, and `unknown` has no `n`

tests/test_retro.py:3704: the `unknown` rows carry a `change` key that no test asserts, and `unknown` has no `n`

Evidence: tests/test_retro.py:3704
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F5. [nit] [correctness] add one assertion that a stop before any commit leaves no row, since the spec's edge-case section names it

tests/test_retro.py:3677: add one assertion that a stop before any commit leaves no row, since the spec's edge-case section names it

Evidence: tests/test_retro.py:3677
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F6. [nit] [correctness] `scripts/retro.py` (`_closing_subject`): the helper is defined after the functions that call it.

`scripts/retro.py` (`_closing_subject`): the helper is defined after the functions that call it. It works, but sits oddly beside `_commands_commit`.

Evidence: reviews/land-1/code.md
Class: code review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code
