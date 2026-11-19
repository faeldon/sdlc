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

## F1. [nit] [correctness] `_trend` compares the unrounded `value` with the `last` read back from the report's cell, which was written through `indicators.number`.

scripts/retro.py:423: `_trend` compares the unrounded `value` with the `last` read back from the report's cell, which was written through `indicators.number`. A figure that rounds to the same cell (for example 0.174 against a written 0.17) could read `up` when the person saw two equal numbers. Compare after rounding `value` the way the table writes it, or confirm `number()` writes full precision.

Evidence: scripts/retro.py:423
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F2. [nit] [correctness] `_minutes` rounds a median response to a whole number.

scripts/retro.py:433: `_minutes` rounds a median response to a whole number. The report above shows a median response of "1" minute in both tiers, so small values lose their trend resolution. This follows the spec's "integers" rule, so it is only worth a Note in REFERENCE.md.

Evidence: scripts/retro.py:433
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F3. [nit] [correctness] `test_the_pillar_sections_show_autonomy_pipeline_and_cost` checks the Speed pipeline terms as bare lowercase substrings ("gates", "bisections").

tests/test_retro.py: `test_the_pillar_sections_show_autonomy_pipeline_and_cost` checks the Speed pipeline terms as bare lowercase substrings ("gates", "bisections"). It would still pass if they appeared anywhere in the Speed section, such as in prose rather than the landing line. Match the landing line's label instead.

Evidence: tests/test_retro.py
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
