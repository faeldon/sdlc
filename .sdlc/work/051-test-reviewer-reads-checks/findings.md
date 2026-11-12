# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

## F1. [nit] [correctness] The new test's docstring claims more than it checks

It says every agent with Bash but the builder "is told never to run one", but the test only
requires that of an agent whose text names `checks.md` (reviewer-code and reviewer-security name
it nowhere, and aren't told). A reader trusts the docstring and thinks those two are covered.

Evidence: tests/test_skills.py:806
Class: a test's description overstating its assertions; none other in this diff.
Disposition: fixed

## F2. [nit] [correctness] The [building] pointer runs into the seed's prose

`Building in .sdlc/work/051-test-reviewer-reads-checks/.` sits on the line directly above the
seed's first prose line, so it renders as one paragraph with it; every earlier `[building]` entry
has a blank line after the pointer.

Evidence: .sdlc/work/inbox.md:455
Class: the register's entry shape; ship deletes this entry, so it lasts only until the commit.
Disposition: fixed
