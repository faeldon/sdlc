# Findings

> What a change's review found, one `## ` section a finding, committed with the change.
> `/sdlc:ship` writes it after every review, and the factory's `carry`, and its landing's rounds,
> write their agents' findings into it; `By:` names who raised one: `fresh` for ship's
> fresh-context reviewer, a factory role (`code`, `test`, …) for an agent, and no line on ship's
> own. A rerun keeps each id, marks one the diff no longer shows `fixed`, and never raises again
> one the person answered `wrong`, `intentional` or `minor`; an agent's `wrong` is its arbiter's,
> never the person's, and the same fault worded differently is one more. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:`, `By:` and `Fix:` lines, counts
> ship's own alone into the `Sdlc-Findings` trailer (its `agents=` says how many it left out),
> words ship's question from the ones proposed `fix`, and `ship` refuses while one is still `open`
> or `fix`. On a diff that touches a sensitive path, this note also says `Fresh review: ran`, or
> `Fresh review: skipped, <why>`. Each of ship's further passes that applies says the same on a
> line of its own: `Security review:`, `Behaviour check:`, `UI review:` and `UX review:`, and
> their findings' `By:` is `ship-security`, `ship-behaviour`, `ship-ui` or `ship-ux`, counted as
> ship's own (`passes=` says how many). A behaviour check that ran ends the file with an
> `## Evidence` section: each command on a `$ ` line, the tail of its output, then `exit: <n>`.

Skill evals: ran, 6 of 9; environment: ship, ship-behaviour, ship-open-finding; run: .sdlc/reports/cases-2026-11-21-4

## F1. [nit] [correctness] R7 says `--preview` takes the same clause flags as `--question`.

scripts/sdlc.py:8308: R7 says `--preview` takes the same clause flags as `--question`. They parse, but `cmd_ship_preview` ignores them without saying so. Refuse them with `--preview`, as the code already refuses clause flags without `--question`, or say in the help text that they are ignored.

Evidence: scripts/sdlc.py:8308
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F2. [nit] [correctness] skills/ship/SKILL.md:Step 5: the cut applies to `--preview`'s output alone, but the commit message goes in the same preview ahead of it.

skills/ship/SKILL.md:Step 5: the cut applies to `--preview`'s output alone, but the commit message goes in the same preview ahead of it. A long message can push the dialog past 40 lines, and nothing says which part to cut. Say that the message counts toward the 40.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F3. [nit] [correctness] the `PREVIEW_NAMES` words are checked with substring `in`, so a key word like `path` or `tag` matches any text that contains it

tests/test_skills.py:263: the `PREVIEW_NAMES` words are checked with substring `in`, so a key word like `path` or `tag` matches any text that contains it

Evidence: tests/test_skills.py:263
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
