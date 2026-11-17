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
> Skill evals: ran, 2 of 3 (cases-2026-11-17-12; cases-2026-11-17-11 failed `intent` instead)

## F1. [important] [correctness] The skills' case intent-product failed its judgment grader

The `intent-product` case scored 0.875 in cases-2026-11-17-12: its judgment grader voted FAIL three
times, reading only the run's last message, the WAIT asked as plain text.

Evidence: .sdlc/reports/cases-2026-11-17-12 (intent-product, judgment); .sdlc/reports/cases-2026-11-17-11 (intent failed the same grader, intent-product passed)
Class: a skill doing what its text forbids
Disposition: wrong
Reason: the person's call: the failure moved between `intent` and `intent-product` across two runs on the same diff, each case passing once; the judge reads only a reply split before its plain-text question, as on 096's first run, so it is the grader's read, not this diff

## F2. [nit] [cost] A rewrapped line in intent's Step 0 runs to 130 columns

`skills/intent/SKILL.md:50`, rewritten to name `work.register`, is 130 columns wide; the skill's
prose wraps near 100.

Evidence: skills/intent/SKILL.md:50
Class: prose left unwrapped after an edit; the file already has nine other lines past 100
Disposition: minor
Reason: the file already holds long lines; not worth a nit of its own
