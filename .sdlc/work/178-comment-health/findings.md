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

## F1. [nit] [correctness] `.sdlc/comment-health.py`:162: `_narration_lines` re-sorts the code-line keys per file and scans linearly for each block's target line (`next(...)`).

`.sdlc/comment-health.py`:162: `_narration_lines` re-sorts the code-line keys per file and scans linearly for each block's target line (`next(...)`). That is fine at 12 files, but `bisect` would be tidier.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F2. [nit] [correctness] `.sdlc/comment-health.py`:233: `hot()` reaches into the loaded module's private `HEAT._git`, as `main()` does too.

`.sdlc/comment-health.py`:233: `hot()` reaches into the loaded module's private `HEAT._git`, as `main()` does too. It is intended by the spec, but the leading underscore is worth a comment, or a public alias in function-heat.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F3. [nit] [correctness] no test pins that a line-1 shebang is left out of the comment count, though the plan records it as a departure

tests/test_comment_health.py: no test pins that a line-1 shebang is left out of the comment count, though the plan records it as a departure

Evidence: tests/test_comment_health.py
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
