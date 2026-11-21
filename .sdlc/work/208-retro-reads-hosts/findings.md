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

## F1. [nit] [correctness] scripts/retro.py:`_discover`: the install's `project` strings are compared to the resolved listed and excluded paths without being resolved first.

scripts/retro.py:`_discover`: the install's `project` strings are compared to the resolved listed and excluded paths without being resolved first. A symlinked or differently spelled install path (for example `/var` against `/private/var` on macOS) could show an already-listed repo as unlisted. Run `Path(p).resolve().as_posix()` on each install before comparing, as R9 says.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F2. [nit] [correctness] scripts/retro.py:`_scrub`: it checks string values only, not dict keys.

scripts/retro.py:`_scrub`: it checks string values only, not dict keys. The keys today all come from fixed vocabularies, so nothing leaks. A comment saying so would stop a later change from adding a host-derived key.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F3. [nit] [correctness] R3 says a listed path under this repo's `.claude/worktrees/` is skipped and counted as `own`.

tests/test_retro_hosts.py:329: R3 says a listed path under this repo's `.claude/worktrees/` is skipped and counted as `own`. Only the main checkout is listed in the fixtures, so the worktree case is never exercised. Add a worktree path to `_listed`.

Evidence: tests/test_retro_hosts.py:329
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: med
By: test

## F4. [nit] [correctness] the `!` exclusion is only shown against a path that doesn't exist, so it would pass even if an excluded host were still read.

tests/test_retro_hosts.py:325: the `!` exclusion is only shown against a path that doesn't exist, so it would pass even if an excluded host were still read. Exclude a real fixture host and assert it is absent from `read`.

Evidence: tests/test_retro_hosts.py:325
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: med
By: test

## F5. [nit] [correctness] R12 says no host figure enters the indicators the next retro reads back.

tests/test_retro_hosts.py:426: R12 says no host figure enters the indicators the next retro reads back. The test compares `retro`'s JSON with and without a list, but doesn't compare the report's indicators block.

Evidence: tests/test_retro_hosts.py:426
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
