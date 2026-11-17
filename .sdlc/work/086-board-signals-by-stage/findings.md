# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

## F1. [nit] [context] REFERENCE.md's new board paragraph runs past 100 columns and names no column

The rewrapped paragraph leaves one line well over the doc's width, and "leaves Needs you for that
stage's column" doesn't say where a change put back to `build` goes. Both reviewers in round 1
raised it; round 2 didn't take it up.

Evidence: docs/REFERENCE.md:457
Class: a doc edit left unwrapped and vague; once here
Disposition: fixed

## F2. [nit] [correctness] No test pins a pending decision at `test`

`column()` and `next_action()` now count a pending blocking decision only at `build`, but the new
test builds one only at `shipped`, so moving the `stage == "build"` gate would fail nothing.

Evidence: scripts/board.py:582, scripts/board.py:608, tests/test_board.py:840
Class: a new gate with only the far side of it tested
Disposition: fixed

## F3. [nit] [correctness] The step track still reads `decision.md` at any stage

`_progress()` takes any `decision` as the run done, so a change put back to `build` sits in the
Build column with every step ticked: the same stage-blind read this change removes from the column
and the next action.

Evidence: scripts/board.py:371
Class: a factory signal read without its stage; the last one in board.py
Disposition: recorded

## F4. [pre-existing] [correctness] A card whose file won't read says `/sdlc:close` at a closed stage

`next_action()` returns `/sdlc:close NNN` for a shipped or dropped change before it looks at
`problems`, so the card sits under Needs you naming a close.

Evidence: scripts/board.py:574-577
Class: a problem outranked by the stage in one reader but not the other
Disposition: recorded

## F5. [pre-existing] [correctness] At phone width Needs you is the last column

Below 760px the columns stack in stage order, so the one that waits on the person is under every
other.

Evidence: scripts/board.html:44-46
Class: layout order that follows the data, not the reader's priority
Disposition: recorded

## F6. [pre-existing] [correctness] The file drawer has no focus trap

The drawer is `aria-modal`, but Tab moves into the page behind its scrim.

Evidence: scripts/board.html:136
Class: a modal without the keyboard behaviour it declares
Disposition: recorded

## F7. [pre-existing] [correctness] The verifier's chip explains itself only in a tooltip

`kept 1 · dropped 2` says whose count it is only in its `title`, which keyboard, touch and
screen-reader users don't get.

Evidence: scripts/board.html:196-198
Class: meaning carried by a tooltip alone
Disposition: recorded
