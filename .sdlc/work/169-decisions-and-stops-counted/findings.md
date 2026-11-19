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

## F1. [nit] [correctness] `autonomy_counts` counts a ledger line with the `SUPERSEDED` and `SETTLED` marks under `defaults` only.

scripts/factory_records.py:643: `autonomy_counts` counts a ledger line with the `SUPERSEDED` and `SETTLED` marks under `defaults` only. A superseded or settled blocking or look line gets no such check. It falls under answered or checked, which is probably right, since the approver settles defaults only. A one-line comment would make that explicit

Evidence: scripts/factory_records.py:643
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F2. [nit] [correctness] scripts/retro.py `_autonomy`: `asked.n` and the per-change figures use all factory changes (`n`).

scripts/retro.py `_autonomy`: `asked.n` and the per-change figures use all factory changes (`n`). `escalations.n` leaves out changes with an unreadable decision. The mix is deliberate under R5, but REFERENCE says only that a decision file no answer reads leaves its change out of `escalations`' `n`. Saying "only" there would help

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F3. [nit] [correctness] R8's rate test lets one ledger give `kept=1, changed=1`, so `kept/(kept+changed)` and `kept/total_defaults` can't be told apart by the 0.5 rate alone.

tests/test_retro.py:2606: R8's rate test lets one ledger give `kept=1, changed=1`, so `kept/(kept+changed)` and `kept/total_defaults` can't be told apart by the 0.5 rate alone. A test with `confirmed` or `settled` lines that outnumber the rest would fail if the denominator changed.

Evidence: tests/test_retro.py:2606
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F4. [nit] [correctness] R8's rate test gives `kept=1, changed=1`, so `kept/(kept+changed)` and `kept/total_defaults` can't be told apart by the 0.5 rate alone.

tests/test_retro.py:2606: R8's rate test gives `kept=1, changed=1`, so `kept/(kept+changed)` and `kept/total_defaults` can't be told apart by the 0.5 rate alone. A ledger where `confirmed` or `settled` lines outnumber the rest would fail if the denominator changed.

Evidence: tests/test_retro.py:2606
Class: test review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: test
