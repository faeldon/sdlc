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

## F1. [nit] [correctness] `_write_ci_cache` formats `checked` by hand with `+00:00`.

scripts/sdlc.py:9860: `_write_ci_cache` formats `checked` by hand with `+00:00`. The update cache probably has a similar helper, and sharing it would remove the duplicate.

Evidence: scripts/sdlc.py:9860
Class: code review, round 1
Disposition: recorded
Theme: refactor
Cost: S
Value: low
By: code

## F2. [nit] [correctness] R3 says nothing is written outside a repo, and only the missing-source cases check for a cache file.

tests/test_base_ci.py: R3 says nothing is written outside a repo, and only the missing-source cases check for a cache file. No test calls `base_ci()` with a home that isn't a repo and asserts it writes nothing.

Evidence: tests/test_base_ci.py
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F3. [nit] [correctness] the `os.replace` temp-file write and `newline="\n"` (R3, R11) are covered only by the existing `tests/test_windows.py` scans, not by a test of this change.

tests/test_base_ci.py: the `os.replace` temp-file write and `newline="\n"` (R3, R11) are covered only by the existing `tests/test_windows.py` scans, not by a test of this change.

Evidence: tests/test_base_ci.py
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F4. [nit] [correctness] tests/test_land.py::test_a_red_base_is_a_signal: the final `clear is False` assertion monkeypatches `_preflight`.

tests/test_land.py::test_a_red_base_is_a_signal: the final `clear is False` assertion monkeypatches `_preflight`. It proves `clear` reads the signal, but not that the real preflight reaches `land_signals()` with the `ci` part.

Evidence: reviews/round-1/test.md
Class: test review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: test
