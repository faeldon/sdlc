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
> Skill evals: skipped, each run's scaffold was killed before any turn, so no grader ran
>
> In cases-2026-11-13-8, ship's scaffold was killed after 169s and ship-open-finding passed; in
> cases-2026-11-13-9, both were, after 135s and 3476s. The new never-reads-a-branch grader never ran.

## F1. [nit] [correctness] A bare pointer to a renamed side file passes the side-file test

`test_a_skill_s_side_files_are_named_by_it_and_hold_no_gate` catches a `skills/<name>/<file>.md`
path naming a missing file, but a bare `` `fresh.md` `` pointer is only checked against the files
that exist, so `SKILL.md` could go on naming a branch file renamed or removed. `SHIP_BRANCHES`'
test keeps what `preflight` names in step with the files, so only the pointer prose can drift.

Evidence: tests/test_skills.py:716
Class: a check intersected with what exists can't see what's missing (R9 covers full paths only)
Disposition: recorded
