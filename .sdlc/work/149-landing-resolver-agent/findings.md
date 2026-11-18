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

## F1. [nit] [correctness] the edited *The factory* paragraph now has a very long line, 4 lines down from the reflow.

AGENTS.md:237: the edited *The factory* paragraph now has a very long line, 4 lines down from the reflow. Re-wrap it near the 100-column width the rest of the file keeps.

Evidence: AGENTS.md:237
Class: code review, round 1
Disposition: recorded
Theme: style
Cost: S
Value: low
By: code

## F2. [nit] [correctness] in `cmd_resolve --continue`, `_stray()` runs before the register is pruned, which is what the spec says.

plugins/factory/scripts/factory.py:6966: in `cmd_resolve --continue`, `_stray()` runs before the register is pruned, which is what the spec says. If `.sdlc/last-id` is still modified in the worktree after `_rebase_settling()`, it would count as stray. Spec R9 says it is staged, and a test covers the clean path, so I'm only flagging it. A test where a conflicting stack also touches `last-id` would settle it.

Evidence: plugins/factory/scripts/factory.py:6966
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F3. [nit] [correctness] the fence test mixes tracked and untracked strays in one flow.

tests/test_train.py:976: the fence test mixes tracked and untracked strays in one flow. A failure message won't say which case broke, so the `refused` helper could take a label

Evidence: tests/test_train.py:976
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F4. [important] [correctness] the card's `next:` line still says "its builder is resolving a conflict".

scripts/board.py:843: the card's `next:` line still says "its builder is resolving a conflict". After this change the resolver does that work, so the card names an agent that isn't running. Change it to "its resolver", or to a neutral "its agent". Update the same wording in `tests/test_board.py:1216` and `:1424`, and in the board paragraph at `docs/REFERENCE.md:579`. The comment at `board.py:836` already says "agent", so only the user-facing string is stale.

Evidence: scripts/board.py:843
Class: ux review, round 1
Disposition: fixed
By: ux
