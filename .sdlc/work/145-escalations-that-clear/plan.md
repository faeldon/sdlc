---
id: 145
slug: escalations-that-clear
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 145 — An escalation the person has dealt with clears without a rebuild · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`: `REASON_RE` and `escalation_reasons()` (R2);
  `LEDGER_RE` gains `look` (R4); `read_ledger()` adds `current` and makes a non-current `look`
  line neither `open` nor `decided` (R6); `cmd_decisions()` files `look` reasons once per
  (round, text) (R3); `_settle_refusal()` refuses a `look` (R5); `_dispose()` confirms only
  `default` lines (already: kept, pinned by a test); `upgrade_answer()` reads only `blocking`
  (already: pinned); `cmd_ask()` lists `look` items and prints `gate`, `next: gate` (R11); copies
  of `sdlc.py`'s hand-gate currency (`_hand_paths()`, `_hand_digests()`, `_hand_hash()`,
  `hand_build()`, `HAND_GATE`) and `hand_gate_cleared()` (R8, R11, R13); `land_parts()` gains
  `escalations`, `land_shown()` prints them (R13); `_record_land()` writes
  `runs/land-times.jsonl` (R19); `WAITS_RE`, `land_step_text()`/`read_land_step()` carry
  `WAITS:` (R22); `LAND_STEPS` gains `wait` and `recheck` (R22, R26); `_train_reading()`'s
  `done()` writes `wait` records (R22); `cmd_accept()` records `recheck` after the commit (R26);
  `_no_verdict()`, `NO_DECISION`, the landing review's problem reworded (R27).
- `scripts/sdlc.py`: `FACTORY_LEDGER_RE` gains `look`; `FACTORY_REASON_RE`,
  `factory_newest_round()` (a copy of `newest_round()`/`build_round()`); `factory_reading()`
  gives `reasons` and `looks`, splitting look lines out of `pending`/`assumed` (R4, R6, R9);
  `needs_of()` (R9); `decide_step()` names decide for `acknowledge` too; `cmd_gate()` allows a
  factory run at `stage: test` (R7); `cmd_status` reads `hand_gate()` for a factory run at `test`.
- `scripts/board.py`: `LEDGER_RE` gains `look`; `_entry()` reads the hand gate for a factory run
  at `test`; `_factory()` splits look lines and gives `reasons`, reworded problems (R27);
  `column()` (R15, R16); `next_action()` (R9's needs, R25); `LAND_TRACK`/`LAND_AT`/`LAND_LABEL`
  gain `checks`, `recheck`, `wait`; `LAND_OPEN` (R21); `read_land_step()` reads `WAITS:`;
  `_land_progress()` (R21, R22); `history_samples()`/`step_samples()` read `land-times.jsonl`
  (R20).
- `scripts/board.html`: `COLUMNS` (R17), the seventh track position, `running` and the wait line.
- `plugins/factory/agents/approver.md`: every reason a line with its kind (R1).
- `plugins/factory/skills/decide/SKILL.md`: `look` items, the `gate` block (R12).
- `docs/REFERENCE.md`: status's needs, *The board*, the hand gate's paragraph (R18).
- `AGENTS.md`: *The board* paragraph says the hand gate also gates a factory run at `test`.
- `plugins/factory/README.md`: where it names the decide skill's items / the hand gate, if it does.
- `tests/fixtures/board/changes/…`: the fixture's columns renamed in its test.
- `tests/fixtures/land-record-cases.json` (new): the shared table for R24's pinned readers.
- `tests/test_factory.py`, `tests/test_land.py`, `tests/test_train.py`, `tests/test_board.py`,
  `tests/test_sdlc.py`, `tests/test_hand_gate.py`, `tests/test_metrics.py`,
  `tests/test_skills.py`: the tests below, and old assertions moved to the new words and columns.

### As built

- `factory.py` gained `look_current()` (R6's rule, read by `read_ledger()`), `hand_gate_state()`
  and `gate_reasons()` (R8, R11) over the hand-gate copies, `escalation_lines()` (R13, read by
  `land_parts()`), `read_land_times()` (R19, R24's reference reader) and `_train_waits()` (R22,
  called from `_train_reading()`'s `done()` for every step but `eject` and `stop`).
- `sdlc.py`'s `factory_reading()` marks each reason `filed` and `cleared`; a look reason with no
  current ledger line still reads `read the escalation` (the spec's edge case).
- `board.py` reads `reasons`/`looks` through `sdlc.factory_reading()` rather than a third copy, so
  the card and `status` can't differ; its R27 copies are `NO_DECISION` and `no_verdict()`;
  `BY_STAGE`, `LAND_OPEN` and `LAND_TIMES_STEPS` are new.
- `decide`'s skill names the hand gate by `ask`'s `then`, never as `sdlc.py gate`:
  `test_gate_is_never_pre_approved` forbids that command in any skill.

## Work order

1. **Reasons in the factory** (R1–R6): `escalation_reasons()`, the `look` ledger kind in
   `factory.py`, filing, `read_ledger()` currency, the three refusals. Approver.md and its test.
   Pin tests on the three `LEDGER_RE` copies updated at once so the gate stays green.
2. **`ask` and `decide`** (R11, R12): items, `gate` block via the hand-gate copy, `next: gate`.
3. **Status and needs** (R7–R10, R14): `factory_reading()` reasons/looks, `needs_of()`,
   `cmd_gate()` at `test`, status and the board reading the hand gate at `test`, `answered()`.
   The intent's R8 test end to end.
4. **Landing question** (R13): `land_parts()`'s `escalations`, `land_shown()`.
5. **Columns** (R15–R18): `column()`, `_seen()`'s Ready rule, `board.html`, the docs; every
   old column assertion moved.
6. **Landing progress** (R19–R24, R26): the times file, history, open-ended steps, `wait`,
   `recheck`, the pinned readers.
7. **Seeds** (R25, R27): the landing-conflict next step, the reworded problems.

## Tests

- R1: `test_skills.py::test_the_approver_gives_every_reason_a_line_with_its_kind`.
- R2: `test_factory.py::test_escalation_reasons_read_the_current_decision_alone`.
- R3: `test_factory.py::test_a_look_reason_is_filed_once` and `…_filed_again_after_a_restart`.
- R4: `test_factory.py::test_a_look_line_is_counted_in_no_ledger_figure` (`_factory_files()`,
  `factory_reading()`, board `_factory()`); existing copy pins.
- R5: `test_factory.py::test_only_the_person_ticks_a_look_line`.
- R6: `test_factory.py::test_a_restart_makes_a_look_line_history`.
- R7: `test_hand_gate.py::test_the_hand_gate_gates_a_factory_run_at_test_alone` and
  `…_is_counted_in_no_factory_figure`.
- R8: `test_board.py::test_a_green_hand_gate_clears_a_gate_reason_until_an_edit` (the intent's).
- R9: `test_sdlc.py::test_needs_of_an_escalation_by_its_reasons` (table).
- R10: `test_land.py::test_nothing_rewrites_decision_md`.
- R11: `test_factory.py::test_ask_lists_look_items_and_the_gate`.
- R12: `test_skills.py` invariants (unchanged tools and WAIT) and a wording test.
- R13: `test_factory.py::test_land_check_shows_how_each_reason_was_cleared`.
- R14: `test_metrics.py::test_a_cleared_escalation_still_measures_as_escalate`.
- R15/R16: `test_board.py::test_hand_and_factory_changes_share_a_column_per_state` and
  `test_a_hand_change_is_ready_by_review_or_a_green_gate_never_a_red_one`.
- R17: `PRECEDENCE`/`BOTH` gain `acknowledge`, `gate it green`, landing-`resolve` + `rebasing`.
- R18: docs read by eye; `test_board.py` pins `COLUMNS` labels.
- R19: `test_land.py::test_each_landing_step_change_writes_a_times_row`.
- R20: `test_board.py::test_landing_step_times_come_from_land_times`.
- R21: `test_board.py::test_an_open_ended_step_never_shows_a_fraction`.
- R22/R23: `test_train.py::test_a_waiting_change_records_what_it_waits_on`,
  `test_board.py::test_a_train_of_three_shows_its_step_place_and_wait`.
- R24: `test_board.py::test_the_land_record_readers_are_pinned_copies` over
  `tests/fixtures/land-record-cases.json`.
- R25: `test_board.py::test_a_landing_conflict_names_its_builder`.
- R26: `test_land.py::test_accept_after_the_commit_records_recheck`; track test.
- R27: `test_board.py::test_the_boards_problem_words_are_the_factorys`; old-word asserts moved.

## Rollback

`git revert` undoes it all. Nothing is written outside the repo. A host's ledgers may by then hold
`(approver round N, look)` lines and folders `runs/land-times.jsonl` files: after a revert the old
`LEDGER_RE` reads a `look` line as no ledger line, and its open box as `GARBLED_LEDGER`, a problem
the person sees, so tick or delete those lines by hand. `land-times.jsonl` is only read by the
board and is harmless left in place.
