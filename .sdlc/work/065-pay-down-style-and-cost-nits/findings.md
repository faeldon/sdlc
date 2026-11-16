# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.
>
> Fresh review: ran

## F1. [nit] [correctness] The workflow pin is a test only a revert can fail

`test_ci_runs_once_per_publish_not_again_for_the_tag` checks that a line was added to the
workflow's trigger. Only undoing the change breaks it, so by the guide it is an acceptance check
for `checks.md`, not a suite test. Its name also claims "once per publish", which only GitHub's
behaviour shows: the manual `gh run list` check lives only in `plan.md`.

Evidence: tests/test_skills.py:1093, guide/review.md:29
Class: a text-pinning test for a one-line config edit; the `RECORD_CLEARS` edit adds none, correctly
Disposition: fixed
By: fresh

## F2. [nit] [cost] The workflow's header comment now parses ambiguously

The spliced "never again for the tag…" clause separates "or by hand on a branch someone pushed"
from the "it runs on" it belongs to, so the sentence reads as if "by hand" were an alternative to
"a commit already checked".

Evidence: .github/workflows/check.yml:3
Class: a clause spliced into an existing sentence; not elsewhere in the diff
Disposition: fixed
By: fresh
