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

## F1. [nit] [correctness] the `--filter`, `--pager` and `--view` refusals match the exact name only, not `--filter-magic-label`.

plugins/factory/scripts/landing.py:921: the `--filter`, `--pager` and `--view` refusals match the exact name only, not `--filter-magic-label`. That is harmless and ugrep takes no prefixes, but a comment saying so would help.

Evidence: plugins/factory/scripts/landing.py:921
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F2. [pre-existing] [contract] `GREP_FOLLOWS` refuses `-O` (BSD's follow-links flag) for every grep, so ugrep's harmless `-O EXT` (search by file extension) is refused too.

plugins/factory/scripts/landing.py:816: `GREP_FOLLOWS` refuses `-O` (BSD's follow-links flag) for every grep, so ugrep's harmless `-O EXT` (search by file extension) is refused too. This is overly strict, not a hole.

Evidence: plugins/factory/scripts/landing.py:816
Class: security review, round 1
Disposition: recorded
By: security

## F3. [nit] [contract] a GNU or BSD grep refusal of `--config` or `---…` says "makes ugrep …", which may confuse a person reading it on a host without ugrep.

plugins/factory/scripts/landing.py:925: a GNU or BSD grep refusal of `--config` or `---…` says "makes ugrep …", which may confuse a person reading it on a host without ugrep. "makes grep (ugrep) …" would be clearer

Evidence: plugins/factory/scripts/landing.py:925
Class: security review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: security

## F4. [nit] [correctness] no case checks a bare `-d dereference-recurse` word that is really a grep pattern, which D2 accepts refusing.

tests/test_train.py:2340: no case checks a bare `-d dereference-recurse` word that is really a grep pattern, which D2 accepts refusing. A pin would document the trade-off.

Evidence: tests/test_train.py:2340
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
