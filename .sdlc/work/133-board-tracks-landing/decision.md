DECISION: ESCALATE

**Why.** The review rounds ran out, and two of three reviewers still ask for changes: ux has three open items and ui has one. Two of those are the same reachable fault: a landing that stopped after its commit tells the person to run `/sdlc:ship`, and `sdlc.py ship` refuses that. The reviewers also disagree about what a base-branch move should record. All six decisions (D1–D6) are defaults that nobody has confirmed. The plan follows the intent, and the gate passed at round 2 (2404 passed). The person has not yet answered what the card should say for each landing state.

## Reconsider the approach

The same thing came back both rounds: **what the card says, and which command it points to, at each landing state**. The code is not what is wrong.
- **Round 1:** a shipped card that was mid-landing said `/sdlc:close`. A stopped card looked ready and showed raw tool output.
- **Round 2:** a stopped card at `shipped` says `/sdlc:ship … by hand`. Several stop reasons are still raw text, such as `by=auto` and the `_amend_record` text.
- **The base-branch move:**
  - In round 1 the code reviewer asked for a `stop`, and the verifier kept that finding.
  - The builder recorded `rebase` instead, and in round 2 the code reviewer turned round and backed that as default D6.
  - ux still insists on the `stop`. ui calls `rebase` a fair reading but leaves the call to the builder or the code reviewer.
  - Both verifiers kept every finding put to them, so no reviewer was wrong. The fault is in the spec.

This is a Tier 1 change with no spec. The intent's four open questions went into the build as defaults, and nothing ever set out the way forward for each pair of stage (`test` or `shipped`) and landing step (running, moved, stopped). The reviewers rebuilt that table one row at a time. Another round of the same loop would just find the next row.

What should change is the spec. Before anything is rebuilt, the person should answer D5 and D6 and settle that table. Then one targeted fix to `next_action()` and the plain wording for `_land_refused()` closes this out. That work is small.

## Open items
- ui: `scripts/board.py:731`: a stop at `shipped` names `/sdlc:ship` by hand. It should name `/sdlc:close`.
- ux: `scripts/board.py:730-733`: the same fault. `sdlc.py ship` refuses a shipped change (sdlc.py:3710).
- ux: `factory.py:4496` and `:4507`: a moved landing records `rebase`, not `stop`. This depends on D6, and the code reviewer's D6 default argues the opposite.
- ux: `factory.py` stop reasons at 4449, 4453, 4456, 4459, 4483, 4486, and the `_amend_record` text at 4362, 4498 and 4509, still reach the card as raw or jargon text, with no `plain` line.

## Decisions to confirm
- D1: the landing record has its own file, `runs/land-step.md`, and `runs/step.md` stays as it is.
- D2: each landing command writes its own step, and `land-verdicts --record` writes the stops.
- D3: gate, review and verify are timed against history. The other steps show elapsed time only.
- D4: a card that has just landed disappears and does not linger as "landed".
- D5: a stopped landing keeps its column, because moving it to Needs you would change the shared `sdlc.needs_of()`.
- D6: after a base-branch move the record says `rebase` with the move count after the move, not `stop` at `close`. This is the one the reviewers disagree on.

## For the person at ship
Look at these first:
1. `scripts/board.py` `next_action()`, lines 727–740: the next-step text for a landing under way and for one that stopped, at `test` versus `shipped`.
2. The two moved paths in `cmd_land_close` in `plugins/factory/scripts/factory.py`, lines 4490–4510, together with `tests/test_land.py:2138`.
3. `_land_refused()` calls without a `plain` line.

No screenshot shows a stopped landing, so its styling has only been checked from the code.

- IMPACT: minor — the board can now show a change's landing track, with its steps, moves and why it stopped, and the factory's landing writes a new `runs/land-step.md` record. Nothing that existed before changes.

## Undone items
- UNDONE: A stopped landing shows on its card but keeps its column; moving it to Needs you would mean `sdlc.needs_of()` (shared with `status`) reading `runs/land-step.md`. → seed: Move a stopped landing's card to Needs you
- UNDONE: `factory.py accept` during a landing records no step: the track shows the gate's position until review starts. → seed: Record a landing step for factory.py accept
- UNDONE: ui: scripts/board.py:731: a landing that stopped at `close` on a card already at `shipped` reads `or /sdlc:ship 012 by hand`. That change is already committed, so `/sdlc:ship` is the wrong step. The by-hand way on for a shipped card is `/sdlc:close NNN`. Use `/sdlc:close` when the stage is in `CLOSED`, and `/sdlc:ship` otherwise. The stop at `close` is recorded in `factory.py:4515` after the ship commit, so this case is reachable. No screenshot shows a stopped landing, so this is from the code, not the image. → seed: A stopped landing at shipped names /sdlc:close by hand, not /sdlc:ship
- UNDONE: ux: plugins/factory/scripts/factory.py:4496 and :4507: the kept round-1 fix is not in. Both moved paths still write `_record_land(root, folder, "rebase")`, and `tests/test_land.py:2138` pins `("rebase", 1, 1)`. The card therefore shows a running rebase with an elapsed timer and "wait for it" after `moved` has handed the change back. Per the kept finding, call `_record_land(root, folder, "stop", ["<base> moved; run land again"])` on both moved paths, before `_amend_record` and `_moved`. Then assert `step == "stop"`, `after == "close"`, the move count, and the reason in the test after the `moved` return. The test at 2138 must change with it. → dropped: D6 decides this. If the person confirms D6's default (`rebase`), the item is done. If they choose `stop`, it gets fixed in this change before landing, not carried as a seed.
- UNDONE: ux: scripts/board.py:730-733: a stopped landing at stage `shipped` (a stop at close, or at review after the commit) says "or /sdlc:ship {id} by hand". `sdlc.py ship` refuses a shipped change ("is shipped: close it with /sdlc:close", sdlc.py:3710), so the person is sent to a refused command. Name the step the stage takes: `/sdlc-factory:land {id}`, or `/sdlc:close {id}` by hand at `shipped`, and `/sdlc:ship {id}` by hand only at `test`. → dropped: this is the same fault as the ui item at board.py:731, which is carried as a seed.
- UNDONE: ux: the stop reasons are still raw git or tool text on the landing paths. They reach the card as `landing stopped: …` without plain words: factory.py:4449 (`git status couldn't be read`), :4453 (`uncommitted outside the change's folder: <paths>`), :4456 (`HEAD isn't the landing's commit, so its record has nothing to be amended into`), :4459, :4483 and :4486 (`landed by=auto, and …`, where `by=auto` is jargon), and the `_amend_record` text passed at :4362, :4498 and :4509. Give each a `plain` line that says what failed and what to do, as `SHIP_REFUSED` and the commit-failed line already do, and keep the raw words in the output. → seed: Plain words for every landing stop reason on the board
