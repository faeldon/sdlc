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
> Skill evals: ran, 1 of 1

## F1. [nit] [cost] Three edited lines run past the docs' 100-column wrap

Step 1's edited line in the close skill, the new sentence ending AGENTS.md's Closing paragraph,
and REFERENCE.md's list of commands `sdlc.py` runs each run long, where the text around them wraps
at 100.

Evidence: skills/close/SKILL.md:77, AGENTS.md:136, docs/REFERENCE.md:101
Class: formatting left by an in-place edit; the same files already hold 20 lines past 100
Disposition: minor
Reason: cosmetic, and long lines are already common in these files; nothing reads the wrap
