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

Fresh review: skipped, the factory's rounds stand in

## F1. [important] [correctness] `judged = landing.checks_sha(folder)[:16]` raises `TypeError` when the change's `checks.md` was removed after `--begin`.

plugins/factory/scripts/factory.py:4431: `judged = landing.checks_sha(folder)[:16]` raises `TypeError` when the change's `checks.md` was removed after `--begin`. `checks_clearance()` then names step `checks` (`record is None or sha is None`), so `_land_task` doesn't refuse and `cmd_agent` crashes on `None[:16]`. The loop wouldn't reach this, because `land_verdict` counts a missing file as PASS. A hand-run `agent --task land-checks` would reach it, and it should be a refusal, not a traceback. Fix: make `checks_clearance()` return `step: "accept"` (nothing to judge, not clear) when `sha is None`. Or refuse in `_land_task` when `checks_sha(folder)` is None. Add a case to `test_land_checks_refuses_outside_a_changed_train_change`.

Evidence: plugins/factory/scripts/factory.py:4431
Class: code review, round 1
Disposition: fixed
By: code

## F2. [nit] [correctness] the edited factory paragraph has two lines over the file's ~100-column wrap (`change calls for it (build_due()).

AGENTS.md:263: the edited factory paragraph has two lines over the file's ~100-column wrap (`change calls for it (build_due()). Landing, in …`, and `approver and the read-only list together, …`). Re-wrap them.

Evidence: AGENTS.md:263
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F3. [nit] [correctness] plugins/factory/skills/land/SKILL.md:~266: the stops sentence has one very long line (`commit whose before names …`).

plugins/factory/skills/land/SKILL.md:~266: the stops sentence has one very long line (`commit whose before names …`). Re-wrap it.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F4. [nit] [correctness] `_train_begin` calls `_preflight` once per change at begin, as the spec says.

plugins/factory/scripts/landing.py:1900: `_train_begin` calls `_preflight` once per change at begin, as the spec says. Where preflight can't be read, it records `checks: []` with a hash. This is safe, since every check then counts as changed, but a one-line comment saying so would help.

Evidence: plugins/factory/scripts/landing.py:1900
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F5. [pre-existing] [contract] gate/build/accept records are trusted by the hash they state, which any agent that can write in the change's folder can write; a script-side signature or a record kept outside the tree would close it

plugins/factory/scripts/landing.py:2180: gate/build/accept records are trusted by the hash they state, which any agent that can write in the change's folder can write; a script-side signature or a record kept outside the tree would close it

Evidence: plugins/factory/scripts/landing.py:2180
Class: security review, round 1
Disposition: recorded
By: security

## F6. [nit] [contract] `grep -R` (and BSD `-S`/`-O`) passes the read-only list and follows a symlink out of the checkout; refuse recursive grep's symlink-following flags, or recursive grep entirely

plugins/factory/scripts/landing.py:866: `grep -R` (and BSD `-S`/`-O`) passes the read-only list and follows a symlink out of the checkout; refuse recursive grep's symlink-following flags, or recursive grep entirely

Evidence: plugins/factory/scripts/landing.py:866
Class: security review, round 1
Disposition: fixed
Reason: weighed S med: handed to the builder's rework, and not raised again
By: security

## F7. [nit] [contract] the docstring says a symlink out is refused "for a word naming an existing path"; say that a program walking the tree itself is not covered

plugins/factory/scripts/landing.py:842: the docstring says a symlink out is refused "for a word naming an existing path"; say that a program walking the tree itself is not covered

Evidence: plugins/factory/scripts/landing.py:842
Class: security review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: security

## F8. [nit] [correctness] the R9 test drives a real train to `accept` and then edits `checks.md`.

tests/test_train.py:2307: the R9 test drives a real train to `accept` and then edits `checks.md`. The edited command is `rm -f bb.txt`, which is off the list, so it never exercises the case where an edit passes R5 but loses the approver's clearance.

Evidence: tests/test_train.py:2307
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F9. [nit] [contract] GNU grep accepts unambiguous long-option prefixes, so `--der`/`--dereference` passes the exact `GREP_FOLLOWS_LONG` match and still follows symlinks while recursing; refuse any `--` word that is a prefix of `--dereference-recursive` (length ≥ 3), or refuse every grep long option not on a short allow-list

plugins/factory/scripts/landing.py:876: GNU grep accepts unambiguous long-option prefixes, so `--der`/`--dereference` passes the exact `GREP_FOLLOWS_LONG` match and still follows symlinks while recursing; refuse any `--` word that is a prefix of `--dereference-recursive` (length ≥ 3), or refuse every grep long option not on a short allow-list

Evidence: plugins/factory/scripts/landing.py:876
Class: security review, round 2
Disposition: recorded
Theme: robustness
Cost: S
Value: med
By: security

## F10. [nit] [correctness] `checks_sha(folder)[:16]` still assumes a non-None value, and only the guard in `_land_task` upstream keeps it safe.

plugins/factory/scripts/factory.py:4431: `checks_sha(folder)[:16]` still assumes a non-None value, and only the guard in `_land_task` upstream keeps it safe.

Evidence: plugins/factory/scripts/factory.py:4431
Class: test review, round 2
Disposition: minor
Reason: past the cap of 5 nits a change files
By: test
