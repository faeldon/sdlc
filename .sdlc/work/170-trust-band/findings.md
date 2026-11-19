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

## F1. [nit] [correctness] scripts/retro.py:~397: `_lead_why()` reads `lead=none`, `lead=bad-opened` and `lead=failed` out of a space-split `coverage` string.

scripts/retro.py:~397: `_lead_why()` reads `lead=none`, `lead=bad-opened` and `lead=failed` out of a space-split `coverage` string. That only works while close appends them as separate words, so a comment saying so would help the next reader.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F2. [nit] [correctness] scripts/retro.py:`_previous_window`: if `since["sha"]` isn't found among the retrospective bounds, `at` falls back to 0.

scripts/retro.py:`_previous_window`: if `since["sha"]` isn't found among the retrospective bounds, `at` falls back to 0. The "previous" window can then silently be the wrong one. An explicit None would be safer, though the case should not occur.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F3. [nit] [contract] `_none_reason()`'s `(\s+\S+=\S*)+$` backtracks badly on a hand-written `Sdlc-Coverage` with many `a=b=c` tokens; use `(\s+[^\s=]+=\S*)+$`

scripts/retro.py:384: `_none_reason()`'s `(\s+\S+=\S*)+$` backtracks badly on a hand-written `Sdlc-Coverage` with many `a=b=c` tokens; use `(\s+[^\s=]+=\S*)+$`

Evidence: scripts/retro.py:384
Class: security review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: med
By: security

## F4. [nit] [contract] `runtime_trailer()` puts no limit on how long a version or model value can be, so an odd transcript value makes a very long trailer line; capping each value (e.g.

scripts/metrics.py:1700: `runtime_trailer()` puts no limit on how long a version or model value can be, so an odd transcript value makes a very long trailer line; capping each value (e.g. 64 chars) would bound it

Evidence: scripts/metrics.py:1700
Class: security review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: security

## F5. [nit] [correctness] scripts/retro.py `_previous_window`: if `since`'s sha isn't among the retrospective bounds, `at` falls back to 0 and the "last window" silently becomes the one before the newest retrospective, which may not be the one before `since`.

scripts/retro.py `_previous_window`: if `since`'s sha isn't among the retrospective bounds, `at` falls back to 0 and the "last window" silently becomes the one before the newest retrospective, which may not be the one before `since`. It's unlikely because `since` comes from the same list.

Evidence: reviews/land-1/code.md
Class: code review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F6. [nit] [correctness] scripts/retro.py `_coverage_line`: a headline block with no `coverage` reads "not given".

scripts/retro.py `_coverage_line`: a headline block with no `coverage` reads "not given". That is right for `metrics=None`, but nothing tests that wording at the `render_report` level.

Evidence: reviews/land-1/code.md
Class: code review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F7. [nit] [contract] `_none_reason()`'s `(\s+\S+=\S*)+$` backtracks badly on a hand-written `Sdlc-Coverage` with many `a=b=c` tokens; use `(\s+[^\s=]+=\S*)+$`

scripts/retro.py:664: `_none_reason()`'s `(\s+\S+=\S*)+$` backtracks badly on a hand-written `Sdlc-Coverage` with many `a=b=c` tokens; use `(\s+[^\s=]+=\S*)+$`

Evidence: scripts/retro.py:664
Class: security review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: security

## F8. [nit] [contract] `runtime_trailer()` puts no limit on how long a version or model value can be, so an odd transcript value makes a very long trailer line; capping each value (e.g.

scripts/metrics.py:1709: `runtime_trailer()` puts no limit on how long a version or model value can be, so an odd transcript value makes a very long trailer line; capping each value (e.g. 64 chars) would bound it

Evidence: scripts/metrics.py:1709
Class: security review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: security

## F9. [nit] [correctness] no test checks that 168's value sentences and 170's coverage lines both appear, in order, in `{{window}}` of one report.

tests/test_retro.py: no test checks that 168's value sentences and 170's coverage lines both appear, in order, in `{{window}}` of one report. This is the one place the conflict was resolved by hand.

Evidence: tests/test_retro.py
Class: test review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: test
