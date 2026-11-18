VERDICT: CHANGES

- CHANGE: plugins/factory/scripts/factory.py:4496 and :4507: the kept round-1 fix is not in. Both moved paths still write `_record_land(root, folder, "rebase")`, and `tests/test_land.py:2138` pins `("rebase", 1, 1)`. The card therefore shows a running rebase with an elapsed timer and "wait for it" after `moved` has handed the change back. Per the kept finding, call `_record_land(root, folder, "stop", ["<base> moved; run land again"])` on both moved paths, before `_amend_record` and `_moved`. Then assert `step == "stop"`, `after == "close"`, the move count, and the reason in the test after the `moved` return. The test at 2138 must change with it.
- CHANGE: scripts/board.py:730-733: a stopped landing at stage `shipped` (a stop at close, or at review after the commit) says "or /sdlc:ship {id} by hand". `sdlc.py ship` refuses a shipped change ("is shipped: close it with /sdlc:close", sdlc.py:3710), so the person is sent to a refused command. Name the step the stage takes: `/sdlc-factory:land {id}`, or `/sdlc:close {id}` by hand at `shipped`, and `/sdlc:ship {id}` by hand only at `test`.
- CHANGE: the stop reasons are still raw git or tool text on the landing paths. They reach the card as `landing stopped: …` without plain words: factory.py:4449 (`git status couldn't be read`), :4453 (`uncommitted outside the change's folder: <paths>`), :4456 (`HEAD isn't the landing's commit, so its record has nothing to be amended into`), :4459, :4483 and :4486 (`landed by=auto, and …`, where `by=auto` is jargon), and the `_amend_record` text passed at :4362, :4498 and :4509. Give each a `plain` line that says what failed and what to do, as `SHIP_REFUSED` and the commit-failed line already do, and keep the raw words in the output.

## Notes

Read: both 1280 and 390 screenshots; `intent.md`; `decisions.md` (D1–D5 all still unticked defaults); `scripts/board.py` (`next_action`, `column`, `_progress`, `_land_progress`, `read_land_step`); `scripts/board.html` (CSS 59–84, COLUMNS 198–206, `progressRow` and `card` 438–503); `plugins/factory/scripts/factory.py` (`read_land_step`, `land_step_text`, `_record_land`, `cmd_land`, `_amend_record`, `cmd_land_close`, `_record_move`, `_moved`); `plugins/factory/skills/land/SKILL.md` (the `moved` round, around lines 144–252); `tests/test_board.py` 2040–2088 and `tests/test_land.py` 2100–2180; fixture `runs/land-step.md` for card 012.

Kept round-1 items checked:
- The `next` for a landing under way is met. `next_action` (board.py:734–738) returns the landing message before any `CLOSED` text, and the 1280 screenshot's card 012 reads "the factory is landing it, at review: wait for it, or /sdlc-factory:land 012 if…", not `/sdlc:close`.
- The stopped card drops the ready look. `.card.landing-stopped` (board.html:68) comes after `.card.ready` (:66), sets `--stop` on the border and `--panel` as background, and `next` for a stop is the stop's text, not the ship one.
- Not a change: the "Ready to close" subtitle (board.html:204) reads "/sdlc:close, or the factory's landing", so it already names the landing. I left it alone.

Not seen: a stopped landing in either screenshot, so the red stop text and its wrapping at 390px are unverified. `.flag` has `overflow-wrap: anywhere`, so it should hold.

Smaller:
- `SHIP_REFUSED` (factory.py:1793) opens "sdlc.py ship refused to ship it". "sdlc.py" is tool jargon to a person; "the ship step refused it: run /sdlc:ship 012 by hand to see why" says the same and is plainer.
- The stop's "at ship" / "at close" uses the internal step names, which match the track's labels. Acceptable as is.

Done well: the stop's `next` is now the way on, not a bare report, and it takes the stop's own words (`after`) into the sentence. The card's "landing stopped:" line lists each problem separately, so a person can read each one.
