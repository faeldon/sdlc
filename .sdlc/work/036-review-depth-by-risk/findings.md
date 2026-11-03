# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:` and `Reason:` lines, and `By: fresh` on a
> finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings` trailer, and
> `ship` refuses while one is still `open`.
>
> Fresh review: not run: this diff isn't deep, since `main` has no `[review]` lists yet.

## F1. [nit] [correctness] A skipped fresh review is caught only by the skill's prose

The script can't tell a deep diff whose fresh reviewer ran and found nothing from one whose reviewer
never ran: a clean fresh review leaves no `By: fresh` entry, and `--fresh-skipped` is the skill's
to pass. A note line `Fresh review: ran` or `skipped, <why>` that `findings` reads, and `ship`
refusing a deep diff without one, would make it mechanical.

Evidence: skills/ship/SKILL.md:235
Class: a guarantee held by a skill's prose where the script could hold it; none other in the diff
Disposition: recorded

## F2. [nit] [correctness] Setup offers risky-path candidates its Step 1 never looks for

Step 2's new question offers "candidates Step 1 found", but Step 1 reads the README, task files,
test layout and entry points, never CI workflows or release scripts.

Evidence: skills/setup/SKILL.md:131
Class: a step that refers to work an earlier step doesn't do; none other in the diff
Disposition: recorded
