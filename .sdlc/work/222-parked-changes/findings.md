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

## F1. [nit] [correctness] `needs_of()` compares `now` with the park's own `DEADLINE`, not the deadline cut to the base branch's `[park] deadline` that `verdicts` uses.

scripts/sdlc.py:5164: `needs_of()` compares `now` with the park's own `DEADLINE`, not the deadline cut to the base branch's `[park] deadline` that `verdicts` uses. A forged record with a far deadline would show no need on the board, while `verdicts` would already stop it. R16 only asks for a need when a supervisor died, so this is cosmetic. Cap it with `capped_park()` in the callers, or accept it.

Evidence: scripts/sdlc.py:5164
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F2. [nit] [correctness] `park --clear` checks only expiry, not `vouched`.

plugins/factory/scripts/factory.py:4034: `park --clear` checks only expiry, not `vouched`. `verdicts` reports an unvouched but parseable record as "remove it, then rerun", while `--clear` refuses until the deadline passes. A person has to `rm` it, which the message already says for a record that won't read. Make `--clear` also remove an unvouched record, or say so in its refusal.

Evidence: plugins/factory/scripts/factory.py:4034
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F3. [important] [contract] `cmd_gate` returns through `_gate_busy()` (`if busy: return _gate_busy(...)`) before it works out `changed` from `before`/`after`.

plugins/factory/scripts/factory.py:3934: `cmd_gate` returns through `_gate_busy()` (`if busy: return _gate_busy(...)`) before it works out `changed` from `before`/`after`. So a busy run that changes the worktree is never seen. A gate's "Tree: changed → FAIL" rule exists to catch a check, running code the builder wrote, that rewrites the change it is judging. On a host that sets `[park] exit`, that code can now edit files, exit with the park code (for example `os._exit(75)` from a test), and leave the edit behind. The next attempt's `before` already holds the edit, so it reads `Tree: unchanged` and goes green, with `Build:` still the hash of the snapshot taken before the edit. Later rounds' reviewers read only `reworked`, worked out from those snapshots, so an edit on a path the rework didn't touch never reaches a reviewer. On `--land`, the gate goes green on a worktree that differs from the commit that lands. Fix: compute `changed` before the busy branch, and treat a busy answer as busy only when nothing changed (`busy = None if changed else busy`). A busy run that changed the tree then becomes a normal `FAIL` attempt with `Tree: changed: …`. Add a test where a check edits a tracked file and exits with `[park] exit`, asserting a FAIL attempt is written and no `runs/parked.md`.

Evidence: plugins/factory/scripts/factory.py:3934
Class: security review, round 1
Disposition: fixed
By: security

## F4. [nit] [contract] `busy_of()`'s `clean()` keeps control characters (ESC and the like), which reach `status` in the terminal; strip C0/C1 before marking

plugins/factory/scripts/factory.py:331: `busy_of()`'s `clean()` keeps control characters (ESC and the like), which reach `status` in the terminal; strip C0/C1 before marking

Evidence: plugins/factory/scripts/factory.py:331
Class: security review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: med
By: security

## F5. [nit] [contract] `[park] exit = 1` is accepted, which makes every ordinary red check a park; warn on 1, or document 75 as the only sensible code

plugins/factory/scripts/factory.py:119: `[park] exit = 1` is accepted, which makes every ordinary red check a park; warn on 1, or document 75 as the only sensible code

Evidence: plugins/factory/scripts/factory.py:119
Class: security review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: security

## F6. [nit] [correctness] the slot-wait test only asserts that "didn't run" appears on stderr, which proves little about the `check` message; assert the "slot" wording too

tests/test_factory_park.py:358: the slot-wait test only asserts that "didn't run" appears on stderr, which proves little about the `check` message; assert the "slot" wording too

Evidence: tests/test_factory_park.py:358
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F7. [nit] [correctness] add a `--build` variant of the busy landing gate, since it takes a separate call path

tests/test_land.py:325: add a `--build` variant of the busy landing gate, since it takes a separate call path

Evidence: tests/test_land.py:325
Class: test review, round 1
Disposition: minor
Reason: past the cap of 5 nits a change files
By: test
