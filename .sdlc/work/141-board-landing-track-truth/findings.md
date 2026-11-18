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

## F1. [nit] [correctness] `stop_text` types `stuck` and `untestable` as `list[str] = ()`.

plugins/factory/scripts/factory.py:1956: `stop_text` types `stuck` and `untestable` as `list[str] = ()`. The annotation says list while the default is a tuple. `list[str] | tuple = ()` or `None` would match what callers pass.

Evidence: plugins/factory/scripts/factory.py:1956
Class: code review, round 1
Disposition: recorded
Theme: style
Cost: S
Value: low
By: code

## F2. [nit] [correctness] `status`'s `needs_of` call for ready (shipped) changes builds a minimal `reading` dict by hand.

scripts/sdlc.py:9986: `status`'s `needs_of` call for ready (shipped) changes builds a minimal `reading` dict by hand. A test pins the resulting output, so this is fine. If `needs_of` later reads more fields at `shipped`, this site is easy to miss.

Evidence: scripts/sdlc.py:9986
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F3. [important] [correctness] The train's stack refusals record git's raw words with no plain line, and the plain line on markers lost its test

141's outcome is a plain line over every landing stop's raw text. Before the rebase, 141 gave the
landing's own rebase a plain line for `_amend_record()`'s refusal (`_amend_plain()`) and for a
failed rebase. The resolution moved that rebase into 139's train, `resolve --onto`, and dropped
both: each records only `why`, so the board shows git's words. The test of the plain line on
"conflict markers left" was in a test 139 rewrote, so it went too, though the code kept the line.

Evidence: plugins/factory/scripts/factory.py:6126 and :6153, `_land_refused(root, folder, {}, why)` with no `plain`; the four assertions a2c05df added to tests/test_land.py:201-204, absent from the resolved file
Class: merge dropped a side (conflict.md), in the train's refusals only
Disposition: fixed
Fix: at factory.py:6126 pass `_amend_plain(why, folder.name.split("-")[0])`; at :6153 pass `f"stacking it onto {onto[:12]} failed: run git status in its worktree to see why, then rerun /sdlc-factory:land {num}"`; in tests/test_train.py, a test that a stray file in a stacking change's worktree, a failed stack and markers left after `resolve --continue` each record a plain line naming the way on, the raw text under it
