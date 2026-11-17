# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

Skill evals: skipped, the diff touches no skill (`cases`' scope is empty).

## F1. [important] [correctness] The spine is said to keep every gate, and the plan's approval isn't kept

The factory README's opening says "every stage, check and gate around them stays the code a person
runs by hand", and `README.md`'s bullet says "the stages, checks, review depth and approvals stay
the ones a change built by hand meets". Under the factory the plan is accepted by the run's
approval, not read in plan mode, which the same README calls the trade this layer makes, and the
supervisor's WAIT is the factory's own. The intent's constraint is no claimed guarantee the code
doesn't make.

Evidence: plugins/factory/README.md:5-7, README.md:164-166, against plugins/factory/README.md:84-85 (the plan accepted by the run's approval)
Class: a doc claiming more than the code does; the rest of the new list is exact
Disposition: fixed
Fix: in plugins/factory/README.md's opening, "while every stage, check and gate around them stays the code a person runs by hand" becomes "while every stage and check around them stays the code a person runs by hand, and ship and close stay the person's"; in README.md's bullet, "the stages, checks, review depth and approvals stay the ones a change built by hand meets" becomes "the stages, checks, review depth, ship and close stay the ones a change built by hand meets"

## F2. [nit] [cost] The gates bullet runs past the docs' 100-column wrap

The edit that took 070's supervisor into the gates item left one line at 147 columns, where the
README's own prose wraps at 100.

Evidence: plugins/factory/README.md:29
Class: a hand edit after a merge left unwrapped; the diff's other lines wrap
Disposition: fixed
Fix: rewrap the gates item in plugins/factory/README.md to 100 columns, its words unchanged
