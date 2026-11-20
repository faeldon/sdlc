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

## F1. [nit] [correctness] skills/retro/SKILL.md:~441: the refusal sentence in Step 6 now runs far past 100 columns.

skills/retro/SKILL.md:~441: the refusal sentence in Step 6 now runs far past 100 columns. Wrap it, since the diff made it longer.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F2. [nit] [correctness] the lead-time-by-way rows still say `none in the window` when the window closed changes but none of that way.

.sdlc/work/189-retro-insights/notes.md: the lead-time-by-way rows still say `none in the window` when the window closed changes but none of that way. R11 named four blocks and not `process.lead`'s ways, so this is outside the spec. Ship will give it a disposition.

Evidence: .sdlc/work/189-retro-insights/notes.md
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F3. [important] [correctness] R6 says a failed `git` step leaves the draft on disk so a rerun finds it, and no test covers it.

tests/test_retro.py: R6 says a failed `git` step leaves the draft on disk so a rerun finds it, and no test covers it. `test_retro_commit_renders_the_insights_and_removes_the_draft` only covers the success path. A change that unlinked the draft before the commit would pass every test. Add a test that makes the commit step fail (for example, a stub `sdlc._git` that raises or returns nonzero on `commit`), then asserts `retro-commit` fails, the draft still exists, and a rerun after the fix commits it and removes it.

Evidence: tests/test_retro.py
Class: test review, round 1
Disposition: fixed
By: test

## F4. [nit] [correctness] the `test_config_reports_the_insights_doc` "off while it doesn't exist" assertion only checks that no warning mentions INSIGHTS, so it is weak

tests/test_retro.py:4867: the `test_config_reports_the_insights_doc` "off while it doesn't exist" assertion only checks that no warning mentions INSIGHTS, so it is weak

Evidence: tests/test_retro.py:4867
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
