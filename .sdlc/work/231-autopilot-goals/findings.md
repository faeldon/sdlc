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

Fresh review: skipped, the factory's rounds stand in

## F1. [nit] [correctness] plugins/factory/scripts/autopilot.py:`cited_paths`: a directory such as `plugins/` or `docs/` counts as a cited path, so a `fixed` or `wrong` LEAVE can pass on a vague pointer.

plugins/factory/scripts/autopilot.py:`cited_paths`: a directory such as `plugins/` or `docs/` counts as a cited path, so a `fixed` or `wrong` LEAVE can pass on a vague pointer. Require `is_file()`, or a path with more than one segment.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F2. [nit] [correctness] plugins/factory/scripts/autopilot.py:`preview`: with an explicit `--goal`, the alternatives pool is the proposed goal plus the first three alternatives, then cut to three again.

plugins/factory/scripts/autopilot.py:`preview`: with an explicit `--goal`, the alternatives pool is the proposed goal plus the first three alternatives, then cut to three again. A goal that sat among those loses the fourth candidate, so the list can come up one short.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: weighed low value: below the factory's filing bar
By: code

## F3. [nit] [correctness] plugins/factory/scripts/autopilot.py:`write_summary`: `## Left for you` prints only `fixed` and `wrong` seeds.

plugins/factory/scripts/autopilot.py:`write_summary`: `## Left for you` prints only `fixed` and `wrong` seeds. `off-goal` seeds appear under `## The plan` ("Off the goal"). That matches R11, but a short pointer in `## Left for you` would help a reader.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: weighed low value: below the factory's filing bar
By: code

## F4. [nit] [contract] say to single-quote a goal given in the person's own words, so `$`, backticks and `"` in it stay literal

plugins/factory/skills/autopilot/SKILL.md:101: say to single-quote a goal given in the person's own words, so `$`, backticks and `"` in it stay literal

Evidence: plugins/factory/skills/autopilot/SKILL.md:101
Class: security review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: med
By: security

## F5. [nit] [correctness] the "empty reason" case rewrites the WAITS line to a bare reason; no case gives a WAVE or LEAVE line an empty reason, which R8 also names

tests/test_autopilot.py:1735: the "empty reason" case rewrites the WAITS line to a bare reason; no case gives a WAVE or LEAVE line an empty reason, which R8 also names

Evidence: tests/test_autopilot.py:1735
Class: test review, round 1
Disposition: minor
Reason: weighed low value: below the factory's filing bar
By: test

## F6. [nit] [correctness] no case puts a `LEAVE` heading-less before any group to show LEAVE is allowed anywhere.

tests/test_autopilot.py:1696: no case puts a `LEAVE` heading-less before any group to show LEAVE is allowed anywhere. Only the group-less WAVE case exists.

Evidence: tests/test_autopilot.py:1696
Class: test review, round 1
Disposition: minor
Reason: weighed low value: below the factory's filing bar
By: test

## F7. [nit] [correctness] the stand-in planner's second reply is still `NONE`, which R8 retires, so `read_plan()` would refuse it.

tests/test_autopilot.py:272: the stand-in planner's second reply is still `NONE`, which R8 retires, so `read_plan()` would refuse it. The test passes, but a valid empty plan (a heading with no WAVE line) would match the contract better.

Evidence: tests/test_autopilot.py:272
Class: test review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: test
