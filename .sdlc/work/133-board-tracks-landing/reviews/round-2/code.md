VERDICT: PASS

No Critical or Required finding. The landing and board rework is done, with two points the round-2 notes got wrong or left open, both below.

- DECISION: [default] Keep the landing's record after a base-branch move as `rebase` with the post-move count (what `factory.py` writes now at 4495–4496 and 4506–4507, and what `test_a_landing_past_its_moves_records_the_stop` pins at line 2138), not a `stop` at `close` as the note asks. The card then says "the factory is landing it, at rebase", and the same run goes straight back to `land` for its rebase, as the land skill's `moved` section says, so a stop would be overwritten at once. Only a session that ends between `moved` and that rerun leaves the card on a step nothing runs; the "if its session ended" clause covers that case. Default: keep `rebase`. If you want the stop for that case, record `stop` at `close` with `"<base> moved; run land again"` after `_record_move` succeeds on both paths, before `_amend_record` and `_moved`, and update line 2138 to match.

## Notes

- NIT: scripts/board.html:204: the "Ready to close" subtitle still reads `/sdlc:close, or the factory's landing`, with `/sdlc:close` first. The round-2 ask was that it not name `/sdlc:close` while a landing is in progress. The card's own `next` is right (`next_action()` checks the landing before `CLOSED`), so this is only the static column hint. Changing it means editing the `who` text and the test at `tests/test_board.py:2084`, which checks only for "landing".
- NIT: scripts/board.py:728–734: a landing under way reads "the factory is landing it, at review: wait for it, or /sdlc-factory:land NNN if its session ended", not the requested "landing under way at <step>: wait for it, or /sdlc-factory:land". The behaviour asked for is in place: the landing is named, and `/sdlc:close` appears only with no record.

Checked against the round-2 notes:

- **Card 012 showing `next: /sdlc:close`** does not reproduce. I built the board fixture into a scratch repo outside the worktree (`/tmp/review-probe-133`) and called `board.state()`. Card 012 (`stage: shipped`, `runs/land-step.md` at `STEP: review`) gets `the factory is landing it, at review: wait for it, or /sdlc-factory:land 012 if its session ended`, and its track reads `now: review`. If the screenshot is still current, it is from an earlier build; re-rendering the fixture settles it.
- **Ready styling and stopped `next`:** done. `.card.landing-stopped` is declared after `.card.ready` with equal specificity, so it wins; a stopped landing's `next` gives the way on, as a stopped build's does.
- **Plain stop wording:** done for the ship refusal (`SHIP_REFUSED`), the commit failure, the rebase, `base`, and the verdict problems (which are factory prose). The close fallback at factory.py:4515 uses sdlc's own refusal sentences, which read plainly enough.

Tests run, with the pytest cache off: `tests/test_land.py -k "move or race or close"` (8 passed), and `tests/test_land.py::test_a_landing_past_its_moves_records_the_stop` plus `tests/test_board.py -k "landing or stopped or ready or moves"` (58 passed, 1 skipped). I did not run the full gate.
