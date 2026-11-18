# Findings

> What a change's review found, one `## ` section a finding, committed with the change.
> `/sdlc:ship` writes it after every review, and the factory's `carry` writes its agents' findings
> into it; `By:` names who raised one: `fresh` for ship's fresh-context reviewer, a factory role
> (`code`, `test`, …) for an agent, and no line on ship's own. A rerun keeps each id, marks one the
> diff no longer shows `fixed`, and never raises again one the person answered `wrong`,
> `intentional` or `minor`; an agent's `wrong` is its verifier's, never the person's, and the same
> fault worded differently is one more. `sdlc.py` reads each heading and its `Evidence:`, `Class:`,
> `Disposition:`, `Reason:`, `By:` and `Fix:` lines, counts ship's own alone into the
> `Sdlc-Findings` trailer (its `agents=` says how many it left out), words ship's question from
> the ones proposed `fix`, and `ship` refuses while one is still `open` or `fix`. On a diff that
> touches a sensitive path, this note also says `Fresh review: ran`, or `Fresh review: skipped,
> <why>`.

Skill evals: ran, 2 of 2

## F1. [nit] [correctness] `zip(ids, seeds, strict=False)` drops the length check the old `strict=True` gave.

plugins/factory/scripts/factory.py:4242: `zip(ids, seeds, strict=False)` drops the length check the old `strict=True` gave. `ids` now also holds the nits' ids, so it is longer than `seeds`. Slice it as `zip(ids[: len(seeds)], seeds, strict=True)`, to match the nits loop below it.

Evidence: plugins/factory/scripts/factory.py:4242
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F2. [nit] [correctness] `land_signals()` calls `nit_findings()` a second time, only to count the nits past the cap.

plugins/factory/scripts/factory.py:3809: `land_signals()` calls `nit_findings()` a second time, only to count the nits past the cap. That re-reads every round for a count. `land_parts()` could return the count with `nits`.

Evidence: plugins/factory/scripts/factory.py:3809
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F3. [nit] [correctness] a nit the cap or the no-path rule turns `minor` keeps its `theme`, `cost` and `value` on the item.

plugins/factory/scripts/factory.py:2008: a nit the cap or the no-path rule turns `minor` keeps its `theme`, `cost` and `value` on the item. That is harmless, because only `file` gates the `Theme:` lines in `finding_section()`. It does make the item's shape inconsistent with an unweighed nit.

Evidence: plugins/factory/scripts/factory.py:2008
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code
