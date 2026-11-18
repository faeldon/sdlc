# Findings

> What a change's review found, one `## ` section a finding, committed with the change.
> `/sdlc:ship` writes it after every review, and the factory's `carry` writes its agents' findings
> into it; `By:` names who raised one: `fresh` for ship's fresh-context reviewer, a factory role
> (`code`, `test`, …) for an agent, and no line on ship's own. A rerun keeps each id, marks one the
> diff no longer shows `fixed`, and never raises again one the person answered `wrong`,
> `intentional` or `minor`; an agent's `wrong` is its verifier's, never the person's, and the same
> fault worded differently is one more. `sdlc.py` reads each heading and its `Evidence:`, `Class:`,
> `Disposition:`, `Reason:`, `By:` and `Fix:` lines, counts ship's own alone into the
> `Sdlc-Findings` trailer (its `agents=` says how many it left out), words ship's question from
> the ones proposed `fix`, and `ship` refuses while one is still `open` or `fix`. On a diff that
> touches a sensitive path, this note also says `Fresh review: ran`, or `Fresh review: skipped,
> <why>`.

## F1. [important] [correctness] `land --close` writes `close` to `runs/land-step.md` at line 4458, before the base-branch move is counted.

plugins/factory/scripts/factory.py:4476: `land --close` writes `close` to `runs/land-step.md` at line 4458, before the base-branch move is counted. When the landing then goes back to rebase (`_record_move` at 4476 and 4486, then `_moved` at 4481 and 4488), the record still says `STEP: close` with the pre-move `MOVES:` count, and `_amend_record` commits that. The card shows "now: close" with a stale "base moved N of k" for a landing that has to run `land` again, which breaks the outcome that the card shows the moves so far. Fix: after a successful `_record_move` on both moved paths, before `_amend_record` and `_moved`, call `_record_land(root, folder, "stop", ["<base> moved; run land again"])`. That way the card shows a stop at `close` with the true move count, and the record is committed with the amend. Add a test in `test_a_landing_past_its_moves_records_the_stop` (or a sibling) that reads `runs/land-step.md` after the `state == "moved"` return and asserts its step, moves and reason.

Evidence: plugins/factory/scripts/factory.py:4476
Class: code review, round 1
Disposition: fixed
By: code

## F2. [nit] [correctness] the new sentence about `runs/land-step.md` runs past the paragraph's wrap width; reflow the paragraph.

plugins/factory/README.md:373: the new sentence about `runs/land-step.md` runs past the paragraph's wrap width; reflow the paragraph.

Evidence: plugins/factory/README.md:373
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F3. [nit] [correctness] `SINCE:` is blank, a value `_record_land()` never writes.

tests/fixtures/board/changes/012-draft-publish/runs/land-step.md: `SINCE:` is blank, a value `_record_land()` never writes. Either give it a timestamp, or say in the fixture test that it is deliberately unknown, so the fixture reads as the writer's output.

Evidence: tests/fixtures/board/changes/012-draft-publish/runs/land-step.md
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F4. [nit] [correctness] notes.md's first item stands: `next_action()` on a card mid-landing still names `/sdlc:close <id>` while the track says the factory is landing it.

notes.md's first item stands: `next_action()` on a card mid-landing still names `/sdlc:close <id>` while the track says the factory is landing it. A `runs/land-step.md` that isn't `stop` should change that line, or the card contradicts itself.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F5. [important] [correctness] a landing that has committed (stage `shipped`) gets `next: /sdlc:close NNN`, while its own track says `now: review` (screenshot card 012).

scripts/board.py:723: a landing that has committed (stage `shipped`) gets `next: /sdlc:close NNN`, while its own track says `now: review` (screenshot card 012). A person following it runs the hand-built close on a factory change, not `land --close`. While `runs/land-step.md` exists, `next` should name the landing: "landing under way at <step>: wait for it, or /sdlc-factory:land". Only with no landing under way should it say `/sdlc:close`. The "Ready to close" subtitle, `/sdlc:close` in board.html:202, has the same problem for a landing in progress.

Evidence: scripts/board.py:723
Class: ux review, round 1
Disposition: fixed
By: ux

## F6. [important] [correctness] scripts/board.py:725 and scripts/board.html:446-454: a stopped landing still reads as ready.

scripts/board.py:725 and scripts/board.html:446-454: a stopped landing still reads as ready. In Ready to ship it keeps the blue `.card.ready` styling, and its `next` is the same "/sdlc:ship, or /sdlc-factory:land with the others ready" as an unstopped card. The only sign of the stop is a red "landing stopped: …" line. Under D5 the card stays in its column, so the card itself has to say it stopped: a stop should drop the ready styling, and its `next` should say the way on, as a stopped build's does. The stop's reason also arrives as raw output, for example `sdlc.py ship refused: <last 500 chars of stderr>` (factory.py:4326). It should be plain words the person can act on.

Evidence: reviews/round-1/ux.md
Class: ux review, round 1
Disposition: fixed
By: ux

## F7. [nit] [correctness] the "Ready to close" subtitle still reads `/sdlc:close, or the factory's landing`, with `/sdlc:close` first.

scripts/board.html:204: the "Ready to close" subtitle still reads `/sdlc:close, or the factory's landing`, with `/sdlc:close` first. The round-2 ask was that it not name `/sdlc:close` while a landing is in progress. The card's own `next` is right (`next_action()` checks the landing before `CLOSED`), so this is only the static column hint. Changing it means editing the `who` text and the test at `tests/test_board.py:2084`, which checks only for "landing".

Evidence: scripts/board.html:204
Class: code review, round 2
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F8. [nit] [correctness] a landing under way reads "the factory is landing it, at review: wait for it, or /sdlc-factory:land NNN if its session ended", not the requested "landing under way at <step>: wait for it, or /sdlc-factory:land".

scripts/board.py:728–734: a landing under way reads "the factory is landing it, at review: wait for it, or /sdlc-factory:land NNN if its session ended", not the requested "landing under way at <step>: wait for it, or /sdlc-factory:land". The behaviour asked for is in place: the landing is named, and `/sdlc:close` appears only with no record.

Evidence: scripts/board.py:728–734
Class: code review, round 2
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F9. [important] [correctness] a landing that stopped at `close` on a card already at `shipped` reads `or /sdlc:ship 012 by hand`.

scripts/board.py:731: a landing that stopped at `close` on a card already at `shipped` reads `or /sdlc:ship 012 by hand`. That change is already committed, so `/sdlc:ship` is the wrong step. The by-hand way on for a shipped card is `/sdlc:close NNN`. Use `/sdlc:close` when the stage is in `CLOSED`, and `/sdlc:ship` otherwise. The stop at `close` is recorded in `factory.py:4515` after the ship commit, so this case is reachable. No screenshot shows a stopped landing, so this is from the code, not the image.

Evidence: scripts/board.py:731
Class: ui review, round 2
Disposition: recorded
By: ui

## F10. [important] [correctness] plugins/factory/scripts/factory.py:4496 and :4507: the kept round-1 fix is not in.

plugins/factory/scripts/factory.py:4496 and :4507: the kept round-1 fix is not in. Both moved paths still write `_record_land(root, folder, "rebase")`, and `tests/test_land.py:2138` pins `("rebase", 1, 1)`. The card therefore shows a running rebase with an elapsed timer and "wait for it" after `moved` has handed the change back. Per the kept finding, call `_record_land(root, folder, "stop", ["<base> moved; run land again"])` on both moved paths, before `_amend_record` and `_moved`. Then assert `step == "stop"`, `after == "close"`, the move count, and the reason in the test after the `moved` return. The test at 2138 must change with it.

Evidence: reviews/round-2/ux.md
Class: ux review, round 2
Disposition: recorded
By: ux

## F11. [important] [correctness] a stopped landing at stage `shipped` (a stop at close, or at review after the commit) says "or /sdlc:ship {id} by hand".

scripts/board.py:730-733: a stopped landing at stage `shipped` (a stop at close, or at review after the commit) says "or /sdlc:ship {id} by hand". `sdlc.py ship` refuses a shipped change ("is shipped: close it with /sdlc:close", sdlc.py:3710), so the person is sent to a refused command. Name the step the stage takes: `/sdlc-factory:land {id}`, or `/sdlc:close {id}` by hand at `shipped`, and `/sdlc:ship {id}` by hand only at `test`.

Evidence: scripts/board.py:730-733
Class: ux review, round 2
Disposition: recorded
By: ux

## F12. [important] [correctness] the stop reasons are still raw git or tool text on the landing paths.

the stop reasons are still raw git or tool text on the landing paths. They reach the card as `landing stopped: …` without plain words: factory.py:4449 (`git status couldn't be read`), :4453 (`uncommitted outside the change's folder: <paths>`), :4456 (`HEAD isn't the landing's commit, so its record has nothing to be amended into`), :4459, :4483 and :4486 (`landed by=auto, and …`, where `by=auto` is jargon), and the `_amend_record` text passed at :4362, :4498 and :4509. Give each a `plain` line that says what failed and what to do, as `SHIP_REFUSED` and the commit-failed line already do, and keep the raw words in the output.

Evidence: reviews/round-2/ux.md
Class: ux review, round 2
Disposition: recorded
By: ux

## F13. [nit] [correctness] the paragraph's reflow leaves a 139-character line, and the wrap at 382 is a lone `pre-approved);`.

plugins/factory/README.md:381: the paragraph's reflow leaves a 139-character line, and the wrap at 382 is a lone `pre-approved);`. Rewrap the paragraph to the file's width.

Evidence: plugins/factory/README.md:381
Class: code review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F14. [nit] [correctness] `A click opens` ends its line and `click opens` starts the next, so the sentence is split across a short line and a long one.

docs/REFERENCE.md:550-551: `A click opens` ends its line and `click opens` starts the next, so the sentence is split across a short line and a long one. Rewrap it to the file's width.

Evidence: docs/REFERENCE.md:550-551
Class: code review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code
