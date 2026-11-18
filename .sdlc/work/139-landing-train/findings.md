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
> `Fresh review: skipped, <why>`.

## F1. [nit] [correctness] AGENTS.md:~236: the factory paragraph's rewritten sentence runs on to one very long line, after `it onto the base past the Close commits before it; fresh moves …`.

AGENTS.md:~236: the factory paragraph's rewritten sentence runs on to one very long line, after `it onto the base past the Close commits before it; fresh moves …`. Re-wrap it, and split the `fresh` clause off so the paragraph stays readable

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F2. [important] [correctness] R14's second part has no test.

tests/test_train.py: R14's second part has no test. Nothing in `tests/` mentions `LOCK_HELD_ENV`, `SDLC_LOCK_HELD`, `_inherit_lock` or `_lock_depth`. A change that stopped passing the variable in `_handoff()` (`scripts/sdlc.py:~4958`) would deadlock a real close and fail no test. Add one that runs a close handing off to the merged script (as `tests/test_adoption.py` and `tests/test_archive.py` do) and asserts it finishes within a timeout. Also assert that `_inherit_lock()` clears the variable, and that it is not in the environment of the child's own subprocesses.

Evidence: tests/test_train.py
Class: test review, round 1
Disposition: fixed
By: test

## F3. [important] [correctness] R8 is tested only for a landing review that keeps a change (`test_a_kept_landing_change_ejects_only_its_change`).

tests/test_train.py: R8 is tested only for a landing review that keeps a change (`test_a_kept_landing_change_ejects_only_its_change`). Its acceptance-check failure on the stacked commit and its reply still unreadable after the one mend are untested. Add a case for each, or fold them into the same test, asserting that only that change is ejected and the others land.

Evidence: tests/test_train.py
Class: test review, round 1
Disposition: fixed
By: test

## F4. [nit] [correctness] tests/test_train.py:~417: the stacking test's last assert, that "merge" is not in the first five reflog subjects, is weak, because rebase reflog lines don't say merge anyway.

tests/test_train.py:~417: the stacking test's last assert, that "merge" is not in the first five reflog subjects, is weak, because rebase reflog lines don't say merge anyway. It would pass if a merge happened further down.

Evidence: reviews/round-1/test.md
Class: test review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: test
