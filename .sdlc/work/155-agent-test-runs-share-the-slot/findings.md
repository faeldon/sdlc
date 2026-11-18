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

## F1. [nit] [correctness] the rewrapped "One gate at a time" bullet leaves one line over the wrap width

plugins/factory/README.md:170: the rewrapped "One gate at a time" bullet leaves one line over the wrap width

Evidence: plugins/factory/README.md:170
Class: code review, round 1
Disposition: recorded
Theme: style
Cost: S
Value: low
By: code

## F2. [nit] [correctness] `FACTORY_CHECK_RE` accepts an optional quote after `.py`, so a quoted path matches, which the test covers.

scripts/metrics.py:132: `FACTORY_CHECK_RE` accepts an optional quote after `.py`, so a quoted path matches, which the test covers. The same quote case isn't handled for `HAND_GATE_RE`, so the two regexes treat quoted paths differently

Evidence: scripts/metrics.py:132
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F3. [nit] [correctness] the new R3 and R4 tests carry no `@pytest.mark.portable` even though the spec says "marked `portable` where they use no shebang fakes".

tests/test_factory.py:4900: the new R3 and R4 tests carry no `@pytest.mark.portable` even though the spec says "marked `portable` where they use no shebang fakes". The two-checks test uses `sleep` and `sh`, so leaving them unmarked is probably right, but the spec's intent is unclear.

Evidence: tests/test_factory.py:4900
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
