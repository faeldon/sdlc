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

## F1. [nit] [correctness] the comment says git's options that "run an external program" are refused, but `git log --show-signature` and `git show --format=%G?` run `gpg`, which the rule as written lets through.

plugins/factory/scripts/factory.py:208: the comment says git's options that "run an external program" are refused, but `git log --show-signature` and `git show --format=%G?` run `gpg`, which the rule as written lets through. The table is narrower than its comment. Either reword the comment to name the two options, or add the signature cases.

Evidence: plugins/factory/scripts/factory.py:208
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F2. [nit] [correctness] the `--co` prefix also refuses `file --cont` (`--continue`), which is harmless and within the strict rule the docstring describes.

plugins/factory/scripts/factory.py:1204: the `--co` prefix also refuses `file --cont` (`--continue`), which is harmless and within the strict rule the docstring describes.

Evidence: plugins/factory/scripts/factory.py:1204
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code
