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

## F1. [nit] [correctness] Close's question template counts the other deletions but the prose names them

Step 2's clause template reads `<ignored paths> (now ignored) and <N> other tracked files`, giving
`other` as a count, but the sentence after it says to name `other`'s paths too, up to five in all.
Two readings of one WAIT question mean two wordings across runs, and spec R6 means the names.

Evidence: skills/close/SKILL.md:113
Class: a skill's literal question and its prose disagreeing; the other clauses in close's Step 2 agree with theirs
Disposition: fixed

## F2. [nit] [correctness] A deleted path that starts with whitespace loses it

`_git()` strips its stdout, so with `-z` the first path keeps its NULs but loses any leading
space, and then appears in neither list under its real name. Git allows such a path, though no
repo is likely to have one.

Evidence: scripts/sdlc.py:4067, scripts/sdlc.py:685
Class: parsing `-z` output through a helper that strips; nowhere else in sdlc.py uses `-z`
Disposition: minor
Reason: a tracked path starting with whitespace is vanishingly rare, and the cost is one mislabelled path in a warning, never a wrong close
