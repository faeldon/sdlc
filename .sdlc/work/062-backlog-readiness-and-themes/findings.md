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
>
> cases-2026-11-16-3: intent scored 1.0 ($0.23).

## F1. [nit] [correctness] `--all` offers the unthemed ideas as one change

`_next_themes()` builds the take-the-theme command for every group, `(no theme)` included, so a
repo with a dozen unthemed ideas is told to take them all as one change: they share no theme, and
the status skill reads the line as a recommendation.

Evidence: scripts/sdlc.py:6007
Class: a grouping's catch-all treated as a group
Disposition: fixed

## F2. [nit] [context] The intent skill's `closes:` step still speaks of one seed

Step 5's "If that seed or bug has an `Issue:` line" reads as one entry; a change taking a theme's
seeds should carry every `Issue:` number of each onto `closes:`.

Evidence: skills/intent/SKILL.md:252
Class: a step left singular when its input became plural
Disposition: fixed
