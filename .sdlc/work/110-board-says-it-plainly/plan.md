---
id: 110
slug: board-says-it-plainly
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 110 — The board says what it means, plainly · plan

> Written by the factory's builder after reading `scripts/board.py`, `scripts/board.html`,
> `sdlc.py`'s `factory_stop()` and `needs_of()`, and the tests that pin them. Tier 1: the intent's
> Approach is the spec; this plan exists because it touches four files.

## Files to change

- `scripts/board.py`: `_stopped()` returns `sdlc.factory_stop(folder)`, so an unreadable record
  is a stop whose `next` is `read runs/stopped.md` (never a `problems` line), as `status` reads it;
  its `problems` parameter and the board's copies of `STOPPED_RE`, `NEXT_RE` and `PROBLEM_RE` go
  (round 1: the first build re-derived the reader); `next_action()` reads the `decide D<n>` items of the `needs` the
  card already holds (`sdlc.needs_of()`, the one place the rules live) and names them first, with
  the problem when there is one too, and with ship or land at an escalation; the rebasing step
  adds that `--abort` keeps the resolved work under `refs/sdlc/end/<branch>`.
- `scripts/board.html`: `.col-head` becomes a two-row grid (heading and count on the first row,
  the `who` subtitle on its own row under the heading), CSS only; an empty column says
  `nothing waiting here` in place of `—`.
- `scripts/sdlc.py`: nothing. `status` already reads an unreadable record as a stop; the board
  moves to it.
- `tests/test_board.py`: 086's `test_an_unreadable_stop_record_is_a_problem` moves to the stop
  reading (renamed, and pinned against `sdlc.factory_stop()` so the two can't drift again);
  `PRECEDENCE` gains `needs` on the pending state, the rebasing text, and an escalation that still
  needs a decision; a `BOTH` map pins the two pairs whose step names both states (a problem with a
  decision at `build`, or at an escalation); 098's assertion on card 004 (a problem and a blocking
  decision) moves to the new text; page tests for the column head and the empty column;
  `test_the_factory_parsing_is_a_pinned_copy` drops the three stop regexes the board no longer
  holds (`sdlc.py`'s own copies stay pinned in `tests/test_metrics.py`).
- `tests/test_sdlc.py`: not edited. `status`'s side is already pinned
  (`test_a_stop_needs_its_way_on`, the `stopped: read runs/stopped.md` line), and the board's new
  test compares its card with `sdlc.factory_stop()` directly.
- `docs/REFERENCE.md` (*The board*): the rebasing step's `refs/sdlc/end/<branch>`, the next step
  following `needs you:`, and the unreadable stop record read alike on the board and in `status`.
  Added during the build: the section describes each of these.

Reused, not re-derived: `sdlc.needs_of()` (the card's `needs`) and `sdlc.factory_stop()` (the
stop record, read once for the board and `status`).

## Work order

1. **The stop record (69).** Test: a garbled `runs/stopped.md` gives a card whose `stopped` equals
   `sdlc.factory_stop(folder)`, `needs == ["stopped: read runs/stopped.md"]`, `next == "read
   runs/stopped.md"`, `problems == []`, column Needs you. Then `_stopped()`.
2. **The next step follows `needs` (57, 70).** Tests: `PRECEDENCE` and a card-level test for a
   `build` card with a problem and a blocking decision, and an ESCALATE at `test` still needing
   `decide D2`. Then `next_action()`.
3. **Rebasing wording (58).** Update the two pinned texts first, then `next_action()`.
4. **The page (52, 56).** Page tests read the CSS and the empty column's node, then `board.html`.

## Tests

- 52: `test_a_column_subtitle_sits_under_its_heading` reads `.col-head`'s CSS: a grid, `.who` on a
  row of its own spanning the head, the count on the heading's row. Manual: open the board at
  1280px and at 400px; each subtitle sits under its heading.
- 56: `test_an_empty_column_says_so` pins the empty column's node built with `h()` and its words.
- 57: `PRECEDENCE`'s problems/decision-pending pair, and `test_a_card_with_a_problem_and_a_decision_names_both`.
- 58: `PRECEDENCE`'s rebasing text and `test_a_change_being_rebased_keeps_its_card` name
  `refs/sdlc/end/<branch>`.
- 69: `test_an_unreadable_stop_record_is_a_stop_as_in_status` (replacing 086's
  `test_an_unreadable_stop_record_is_a_problem`).
- 70: `PRECEDENCE`'s new `escalation pending` state, and the card-level test on a real folder.

## Rollback

`git revert` undoes all of it: the board writes nothing, so no data or state outlives the code.
