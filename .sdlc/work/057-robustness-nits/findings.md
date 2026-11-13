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

## F1. [nit] [correctness] A failed prepare or commit lists prepare's build output as after-bump's

`restore()` now recomputes `untracked` against everything untracked since after-bump began, so
when `prepare` built into an untracked path (`npm pack`'s tarball) and the commit then failed,
that file is listed under `untracked`, which the release skill reads as what after-bump left.

Evidence: scripts/sdlc.py:4968
Class: a report field whose meaning widens with the fix
Disposition: fixed

## F2. [nit] [cost] A line in the factory review skill runs past 100 columns

The new sentence in Step 3 leaves one prose line at 112 characters, where the skill's prose wraps
at 100.

Evidence: plugins/factory/skills/review/SKILL.md:84
Class: an edit not reflowed
Disposition: fixed
