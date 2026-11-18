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

## F1. [nit] [correctness] `tests/test_factory.py` (the `git log --format %G?` and `git log --pretty %GF` rows) and `plugins/factory/scripts/factory.py` (the next-word branch in `_git_reads()`): in git 2.56, `--format` without `=` is unrecognised, and `--pretty` without `=` takes no value.

`tests/test_factory.py` (the `git log --format %G?` and `git log --pretty %GF` rows) and `plugins/factory/scripts/factory.py` (the next-word branch in `_git_reads()`): in git 2.56, `--format` without `=` is unrecognised, and `--pretty` without `=` takes no value. So the separate-word form never reaches gpg. The refusal is harmless over-refusal, and the branch can stay as cheap conservatism. Just don't describe it as a form git accepts.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F2. [nit] [correctness] `factory.py`, the `GIT_RUNS` entry `("--show-signature", len("--show-signature"))`: the length is the whole name, so a plain equality check would read more simply.

`factory.py`, the `GIT_RUNS` entry `("--show-signature", len("--show-signature"))`: the length is the whole name, so a plain equality check would read more simply. Optional.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F3. [nit] [correctness] `factory.py`, `GIT_RUNS`: a literal `%%G` is also refused.

`factory.py`, `GIT_RUNS`: a literal `%%G` is also refused. That is a conservative over-refusal and costs only a mend. The comment already admits it in the intent; it could say so in code too. Optional.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code
