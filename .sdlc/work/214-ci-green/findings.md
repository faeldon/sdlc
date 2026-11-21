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

## F1. [nit] [correctness] `_hand_digests` runs `git hash-object` once per call and ignores its stderr.

scripts/sdlc.py:3076: `_hand_digests` runs `git hash-object` once per call and ignores its stderr. If it fails, the fallback silently hashes raw bytes, so a git failure could make a record read stale only on the next run. That is safe, but a one-line comment saying so would help.

Evidence: scripts/sdlc.py:3076
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F2. [nit] [correctness] tests/test_windows.py:~300: `_unencoded` skips an `open` whose mode is not a constant, so it counts that call as `"r"`.

tests/test_windows.py:~300: `_unencoded` skips an `open` whose mode is not a constant, so it counts that call as `"r"`. That is acceptable for now. A dynamic mode could be flagged instead.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F3. [nit] [contract] `_hand_digests` is now a 15-line copy of `sdlc.py`'s, kept the same by hand.

plugins/factory/scripts/factory.py:3073: `_hand_digests` is now a 15-line copy of `sdlc.py`'s, kept the same by hand. Pin the two bodies equal in `tests/test_hand_gate.py`, as the repo's other copies are pinned, so a fix to one can't skip the other

Evidence: plugins/factory/scripts/factory.py:3073
Class: security review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: med
By: security

## F4. [nit] [correctness] `_lost()`'s new `and not _only_time_wait(port)` branch is proved only by the existing socket test, which exercises it on Linux only.

tests/test_factory_ui.py:474: `_lost()`'s new `and not _only_time_wait(port)` branch is proved only by the existing socket test, which exercises it on Linux only. No test combines a refused bind with a stubbed table; the container run is the only proof.

Evidence: tests/test_factory_ui.py:474
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F5. [nit] [correctness] the `_hand_digests()` fallback is untested.

tests/test_hand_gate.py:145: the `_hand_digests()` fallback is untested. It hashes a path holding a newline with sha256, and covers a failed `hash-object`.

Evidence: tests/test_hand_gate.py:145
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
