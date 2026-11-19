# Findings

> What a change's review found, one `## ` section a finding, committed with the change.
> `/sdlc:ship` writes it after every review, and the factory's `carry`, and its landing's rounds,
> write their agents' findings into it; `By:` names who raised one: `fresh` for ship's
> fresh-context reviewer, a factory role (`code`, `test`, …) for an agent, and no line on ship's
> own. A rerun keeps each id, marks one the diff no longer shows `fixed`, and never raises again
> one the person answered `wrong`, `intentional` or `minor`; an agent's `wrong` is its verifier's,
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

## F1. [nit] [correctness] `_is_process` also skips `.sdlc/setup.json` (`sdlc.MANIFEST`), which R3 doesn't list.

scripts/retro.py:377: `_is_process` also skips `.sdlc/setup.json` (`sdlc.MANIFEST`), which R3 doesn't list. The path is under `.sdlc/` anyway. The skip only stops a change that touched just `setup.json` from counting as process work. REFERENCE.md says so, but the spec doesn't. Drop the skip or add it to the spec.

Evidence: scripts/retro.py:377
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F2. [nit] [correctness] scripts/retro.py:~560: `_milestone_follow` can't see a milestone's seed that was retired with `inbox-commit`, so it reads `carried` where `_seed_follow` reads `dropped`.

scripts/retro.py:~560: `_milestone_follow` can't see a milestone's seed that was retired with `inbox-commit`, so it reads `carried` where `_seed_follow` reads `dropped`. The builder filed this in `notes.md`. It is worth a seed.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F3. [nit] [correctness] the new `bg` regex counts an unquoted `&` inside a URL such as `curl x?a=1&b=2`.

scripts/metrics.py:746: the new `bg` regex counts an unquoted `&` inside a URL such as `curl x?a=1&b=2`. That is a real background `&` in shell, so this is correct, but a test case for it would pin the choice.

Evidence: scripts/metrics.py:746
Class: code review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: code

## F4. [nit] [correctness] `test_retro_and_its_report_show_the_same_figures` compares only work mix and time to users with the report, and has no assertion on the follow-through sentence.

tests/test_retro.py:2126: `test_retro_and_its_report_show_the_same_figures` compares only work mix and time to users with the report, and has no assertion on the follow-through sentence. The spec asks that the report and the JSON not disagree. The other test checks the report text, but follow-through is checked only in the JSON tests.

Evidence: tests/test_retro.py:2126
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: med
By: test

## F5. [nit] [correctness] R14 (the docs) has no test, as the spec says.

tests/test_retro.py: R14 (the docs) has no test, as the spec says. Nothing here checks that `REFERENCE.md` and the retro skill's Step 0 name the three keys.

Evidence: tests/test_retro.py
Class: test review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: test
