---
id: 107
slug: board-needs-you
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 107 — The board and status say what each change needs from you · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `needs_of(rec)` and `answered(rec)` (pure, beside `factory_stop()`);
  `FACTORY_RECONSIDER`; `factory_reading(folder)` (decision, pending, assumed, reconsider,
  ledger line count, the R6 problem; never raises); the `status` dispatch loop sets `needs` and
  `answered` on each open record; `print_status()` ends with `■ What needs me`.
- `scripts/board.py`: `RECONSIDER` copy; `_factory()` gains `reconsider`, `ledger_lines` and the
  R6 problem (worded by `sdlc.GARBLED_LEDGER`, so the two can't drift); `_entry()` sets
  `spec_filled`, then `needs`/`answered` through `sdlc.needs_of` / `sdlc.answered` once `problems`
  is final; `column()` follows `needs`.
- `scripts/board.html`: the `needs you:` line and the `escalated: answered` badge in `card()`;
  `render()`'s key built by a replacer from what is shown; focus put back after a rebuild;
  `aria-live` moved from `#board` to `#status`; the time in a new `#polled` span; `#status` set
  only when its words change; Needs you's and Ready to ship's `who`.
- `tests/test_sdlc.py`: `needs_of` from dicts (R1–R5, R7, R8), `test_needs_of_reads_nothing`.
- `tests/test_board.py`: R5, R6, R9 (022's expectation and a ticked-ledger case), R8's assertion,
  R10, R11/R12 (status run through `main()` on the board's own fixture, so the two are compared on
  the same folders), R13–R15; the pinned-copy test gains `RECONSIDER`; the old
  `JSON.stringify([NARROW.matches, st.changes])` pin becomes R13's.
- `tests/test_metrics.py`: `FACTORY_RECONSIDER` pinned to `factory.RECONSIDER`.
- `docs/REFERENCE.md`: *The board* and the `status` paragraph. `skills/status/SKILL.md`: names
  `■ What needs me` (prose only, no new command).

Reused: `factory_stop()`, `FACTORY_DECISION_RE`, `FACTORY_LEDGER_RE`, `is_unfilled()` (through
`rec["unfilled"]`), the board's `_factory()` reading, `h()`, `ago()`, `dur()`, `CSS.escape` as
`closeDrawer()` uses it.

## Work order

1. **`needs_of` and `answered`**, pure, with their dict-driven tests (R1–R5, R7, R8). Nothing calls
   them yet; the tree works.
2. **The board's column**: `_factory()` reads `reconsider`, `ledger_lines` and the R6 problem;
   `_entry()` sets `needs`/`answered`; `column()` follows `needs`. Tests: R5, R6, R8, R9 on real
   folders, the RECONSIDER pin.
3. **Status**: `FACTORY_RECONSIDER` and `factory_reading()`, the dispatch sets `needs`/`answered`,
   `print_status()` ends with `■ What needs me`. Tests: R11 (against the board on the same
   folders), R12, the metrics pin.
4. **The page**: card line and badge (R10), render key (R13), focus (R14), `aria-live` (R15).
   Tests read the page's script.
5. **Docs** (R16), then the gate.

## Tests

- R1: `test_needs_of_reads_nothing` (fails on any `Path` method, `open` or subprocess while it runs).
- R2: `test_a_stop_needs_its_way_on`. R3: `test_a_blocking_decision_needs_its_id`.
- R4: `test_an_escalation_needs_what_its_ledger_holds`. R7: `test_a_written_unapproved_spec_needs_approval`.
- R5: `test_an_answered_escalation_is_ready_to_ship` (board, real folder).
- R6: `test_a_malformed_open_line_keeps_the_escalation` (board and status).
- R8: `test_a_file_that_wont_read_needs_the_person_at_any_stage` gains the `fix:` assertion.
- R9: `test_each_factory_signal_counts_only_at_its_stage` (022 now needs `read the escalation`; a
  new 028 with a ticked ledger is `ready`).
- R10: `test_a_needs_card_names_what_it_needs`. R11: `test_status_ends_with_what_needs_me`.
- R12: `test_status_records_only_gain_keys`. R13: `test_the_render_key_holds_what_is_shown`.
- R14: `test_a_rebuild_puts_focus_back`. R15: `test_aria_live_sits_on_the_status_line_alone`.
- R16: none; the docs are read at ship's `context` pass.
- Manual (what no test reaches): Tab onto a card, wait past a few polls, focus stays; VoiceOver is
  quiet between polls.

## Rollback

`git revert` undoes all of it: the board and `status` write nothing, and no record, file or
config key is added that anything else reads. Nothing outside the repo is touched.
