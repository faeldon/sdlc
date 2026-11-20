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

## F1. [nit] [correctness] `_vouch()` calls `closing._unlock` but `_try_lock` from the local module.

scripts/sdlc.py:3283: `_vouch()` calls `closing._unlock` but `_try_lock` from the local module. Both work, but a one-line comment would say why the pair is split.

Evidence: scripts/sdlc.py:3283
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F2. [nit] [correctness] the spec's R9 requires a test of two writers at once.

tests/test_records_ledger.py: the spec's R9 requires a test of two writers at once. One exists (`test_two_writers_at_once_leave_whole_lines`), but it only covers `factory.py`'s writer and not core's copy under the same lock.

Evidence: tests/test_records_ledger.py
Class: code review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: code

## F3. [nit] [contract] "An agent editing the change's worktree can't forge one" overstates the protection when the builder and resolver have Bash.

plugins/factory/README.md: "An agent editing the change's worktree can't forge one" overstates the protection when the builder and resolver have Bash. Say that it protects against the Edit and Write tools, not against a shell that can reach the git common dir

Evidence: plugins/factory/README.md
Class: security review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: med
By: security

## F4. [nit] [contract] check again that `earlier` is vouched when it's read after the run, not only before the slot wait

plugins/factory/scripts/factory.py:3358: check again that `earlier` is vouched when it's read after the run, not only before the slot wait

Evidence: plugins/factory/scripts/factory.py:3358
Class: security review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: med
By: security

## F5. [nit] [correctness] the writer test runs 400 locked appends across two processes, which may be slow on a loaded machine; a smaller count would still prove whole lines

tests/test_records_ledger.py:152: the writer test runs 400 locked appends across two processes, which may be slow on a loaded machine; a smaller count would still prove whole lines

Evidence: tests/test_records_ledger.py:152
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F6. [nit] [correctness] the comment still says the ledger "guards against a write in a worktree, never one into the git common dir".

plugins/factory/scripts/factory.py:2898: the comment still says the ledger "guards against a write in a worktree, never one into the git common dir". Use the docs' wording (the Edit and Write tools, not a shell that can reach the git common dir).

Evidence: plugins/factory/scripts/factory.py:2898
Class: code review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F7. [nit] [contract] the ledger comment still says "guards against a write in a worktree"; reword it to match the docs (Edit and Write tools, not a shell that can reach the git common dir)

plugins/factory/scripts/factory.py:2896: the ledger comment still says "guards against a write in a worktree"; reword it to match the docs (Edit and Write tools, not a shell that can reach the git common dir)

Evidence: plugins/factory/scripts/factory.py:2896
Class: security review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: security

## F8. [nit] [correctness] the ledger's code comment still says "It guards against a write in a worktree", which is looser than the docs now say; word it as Edit and Write tools, not a shell that reaches the git common dir

plugins/factory/scripts/factory.py:2898: the ledger's code comment still says "It guards against a write in a worktree", which is looser than the docs now say; word it as Edit and Write tools, not a shell that reaches the git common dir

Evidence: plugins/factory/scripts/factory.py:2898
Class: test review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: test
