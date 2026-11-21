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

Skill evals: ran, 3 of 3; run: .sdlc/reports/cases-2026-11-21-1
Fresh review: skipped, the factory's rounds stand in

## F1. [nit] [correctness] the register paragraph now has a line well over 100 characters, because "Each line's command is `/sdlc:intent <id>`." was glued onto the end of the new clause.

docs/REFERENCE.md:508: the register paragraph now has a line well over 100 characters, because "Each line's command is `/sdlc:intent <id>`." was glued onto the end of the new clause. Rewrap it

Evidence: docs/REFERENCE.md:508
Class: code review, round 1
Disposition: recorded
Theme: style
Cost: S
Value: low
By: code

## F2. [nit] [correctness] the two lines edited for `origin:` run past the file's wrapping width.

skills/intent/batch.md:34: the two lines edited for `origin:` run past the file's wrapping width. Rewrap them

Evidence: skills/intent/batch.md:34
Class: code review, round 1
Disposition: recorded
Theme: style
Cost: S
Value: low
By: code

## F3. [nit] [contract] `origin_trailer()` catches every `Exception`, not just a git or read failure, so a coding error there would make origins quietly unknown on every close instead of failing a test; `fix_trailers()` does the same

scripts/closing.py:558: `origin_trailer()` catches every `Exception`, not just a git or read failure, so a coding error there would make origins quietly unknown on every close instead of failing a test; `fix_trailers()` does the same

Evidence: scripts/closing.py:558
Class: security review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: security

## F4. [nit] [correctness] `test_idea_and_bug_offer_an_origin_line` only asserts that `Origin: self` is absent from the skill text.

tests/test_skills.py: `test_idea_and_bug_offer_an_origin_line` only asserts that `Origin: self` is absent from the skill text. It would not catch the skills telling the person to write `self` in other words

Evidence: tests/test_skills.py
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
