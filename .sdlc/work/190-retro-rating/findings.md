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

## F1. [nit] [correctness] `_experience_text` does `table = _table(..., [[..., rating, before, ...]])`.

scripts/retro.py:2425: `_experience_text` does `table = _table(..., [[..., rating, before, ...]])`. A `None` rating relies on `_table` rendering it as `—`. A test pins this, but the `—` spelling is implicit.

Evidence: scripts/retro.py:2425
Class: code review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: code

## F2. [nit] [correctness] `_last_experience` does `int(rating)` on the table cell.

scripts/retro.py:2467: `_last_experience` does `int(rating)` on the table cell. A hand-edited report with a non-numeric cell would raise instead of reading back as no rating. Guard it, or catch `ValueError`.

Evidence: scripts/retro.py:2467
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F3. [nit] [correctness] `test_a_rating_with_no_line_says_so` takes a `tmp_path` fixture it never uses

tests/test_retro.py: `test_a_rating_with_no_line_says_so` takes a `tmp_path` fixture it never uses

Evidence: tests/test_retro.py
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
