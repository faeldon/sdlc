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
> Skill evals: ran, 2 of 2 (`intent`, `intent-product`, run cases-2026-11-17-5, $0.60).

## F1. [nit] [correctness] No grader checks R4's wording, which R11 says both cases check

R11 says both cases run with no factory enabled and so also check R4's question. But the new
case's `asks-the-question` regex ends at `serving …`, so a run asking the factory form, or
a regression in the endings, would still pass. Both questions in this run end
`(yes / yes, without plan mode / …`, so the tighter pattern matches them.

Evidence: evals/intent-product/graders/asks-the-question.md:4; code reviewer round 1 (Optional, R11)
Class: requirement only partly tested; the existing `intent` case has the same gap, outside this diff
Disposition: fixed

## F2. [nit] [correctness] The factory answer's register edit points at the main checkout's register

With `yes, for the factory` the session stays in the main checkout, where Step 0's `config` ran,
so `work.register` there is the main checkout's `inbox.md`. Step 5 still says to tag seeds in
"the worktree's register, the file `config`'s `work.register` names". If a run takes the path it
was given, it edits main's register: the `[building]` tag misses the change's branch, and the
main checkout is left dirty, which `inbox-commit` then refuses.

Evidence: skills/intent/SKILL.md:248, skills/intent/SKILL.md:264
Class: an instruction that names a path through `config` after the session's checkout changes
Disposition: fixed

## F3. [nit] [correctness] `factory_enabled` lets the first of two factory keys decide

When one settings file names `sdlc-factory@` from two marketplaces, the first key decides, even
if it is `false` and the second is `true`.

Evidence: scripts/sdlc.py:605
Class: first-match where any-match is meant
Disposition: minor
Reason: two marketplaces both carrying the factory in one settings file is unlikely, and a wrong answer only hides an option, which is the side the design errs to

## F4. [nit] [cost] Intent's skill text has an over-long line and a stray short one

Step 0's added note leaves `Note git.base too:` on a line well past the file's width, and
Step 4 breaks after "Starting plan mode", leaving a short line. Neither changes the meaning.

Evidence: skills/intent/SKILL.md:58, skills/intent/SKILL.md:205
Class: wrapping left by an edit
Disposition: fixed
