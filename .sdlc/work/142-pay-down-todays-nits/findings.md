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
> `Fresh review: skipped, <why>`.

## F1. [nit] [correctness] the new "unverified" case asserts only `stuck == []`.

tests/test_factory.py:1676: the new "unverified" case asserts only `stuck == []`. Also asserting `next == "rework"` would pin the full outcome, as the neighbouring cases do.

Evidence: tests/test_factory.py:1676
Class: code review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: code

## F2. [nit] [correctness] `.sdlc/work/142-pay-down-todays-nits/build/land-4.md` is missing.

`.sdlc/work/142-pay-down-todays-nits/build/land-4.md` is missing. The prompt names it as the builder's conflict-resolution record, but only `land-1.md` and `land-3.md` exist, so I could not read the builder's account of this round's resolutions. I judged the diff directly, and it shows no conflict damage.

Evidence: reviews/land-4/code.md
Class: code review, landing round 4
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code
