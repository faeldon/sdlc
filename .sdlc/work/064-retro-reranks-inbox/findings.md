# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

## F1. [nit] [context] The retro skill's description doesn't say it re-ranks

The frontmatter description, what the skill list shows and what decides when `/sdlc:retro` is
reached for, still says it rewrites the direction doc and commits it "with the seeds": the
re-rank, now part of its one approval, goes unmentioned.

Evidence: skills/retro/SKILL.md:3
Class: a skill's summary left behind its body
Disposition: fixed
