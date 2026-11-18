---
id: 151
slug: status-by-board-states
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 151 — status groups its sections by the board's columns · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: gains `BY_STAGE`, `column()`, `seen_stage()`, `touched_paths()` and
  `rebasing_branches()`, moved unchanged from `board.py` (its `sdlc.<name>` calls become direct
  ones), beside `needs_of()` and `answered()`; a new `FACTORY_LAND_STEPS` and
  `factory_landing(folder, stage)`. `main()`'s status branch gives each open record and each
  ready-to-close one a `column`, and adds shipped or dropped changes a stopped rebase holds to
  `a["ready"]` (a new `held_by_rebase()`, shaped as `ready_to_close()`'s records).
  `print_status()` groups by `_by_state()` (a record printed without a `column`, as two
  `test_sdlc.py` tests print `analyze()` alone, sits by its stage) and prints the five states
  (`STATUS_STATES`), ending with `■ Needs you`; the change line and the close line become helpers
  (`_change_lines()`, `_close_line()`).
- `scripts/board.py`: loses `BY_STAGE`, `column()`, `_seen()`, `_touched()`, `_rebasing()`;
  `_entry()` sets `in_flight` from `sdlc.factory_landing()`, then `seen` from `sdlc.seen_stage()`
  and `column` from `sdlc.column()`; `_plan_hint()` calls `sdlc.touched_paths()`; `state()` and
  `_on_board()` call `sdlc.rebasing_branches()`. Its docstring's "ready to close" goes.
- `tests/test_board.py`: the new tests R1, R3, R4, R6, R7, R9, R12; `test_status_never_loads_the_board`
  keeps its source check and now runs `status` with `_load_board` refusing (R10);
  `test_status_ends_with_what_needs_me` becomes `test_status_ends_with_needs_you`, and
  `test_status_lists_a_stopped_landing_under_what_needs_me` becomes `…_under_needs_you`; the status
  tests that split on `■ What needs me` or `■ Ready to close` read the new headings;
  `test_status_records_only_gain_keys` expects `column`. `_hand_at_state()` and
  `_factory_at_state()` take an optional name, since their default names clash across states
  (`planned` and `landing` are both 7 letters) once R9 makes all of them in one repo.
- `tests/test_sdlc.py` / `tests/test_next_up.py`: any status test reading the old headings follows
  (none found but `test_board.py`'s; R11 says the others pass unchanged).
- `skills/status/SKILL.md`: *Needs you* last; precedence step 2 reads a `→ /sdlc:close` line under
  Landing; the five states named.
- `skills/close/SKILL.md`: the changes under **Landing** with a `→ /sdlc:close` line.
- `plugins/factory/skills/decide/SKILL.md`: `■ Needs you`.
- `docs/REFERENCE.md`: status's sections, and the "reads only what it already reads" line.
- `AGENTS.md`: *The board* paragraph's pointers to `seen_stage()` and `column()` in `sdlc.py`.

## Work order

1. **Move the rule (R1, R2, R7's `rebasing_branches`).** Red: `test_the_column_rule_is_sdlcs_alone`.
   Green: move the five names into `sdlc.py`, the board calling them. The whole `test_board.py`
   stays green, proving the move changed nothing.
2. **A landing in flight, one reader (R3, R4).** Red: `test_factory_land_steps_match_the_boards_track`
   and the board half of `test_the_board_and_status_read_a_landing_in_flight_alike`. Green:
   `FACTORY_LAND_STEPS`, `factory_landing()`, the board's `entry["in_flight"]`, `column()` reading it.
3. **Status reads the column (R5, R10).** Red: `test_status_records_only_gain_keys` expecting
   `column`, `test_status_never_loads_the_board` running status. Green: the reading in `main()`.
4. **Status prints the states (R6, R7, R8, R9, R11).** Red: `test_status_prints_the_board_states_in_order`,
   `test_status_lists_a_change_closing_or_rebasing_under_landing`, `test_status_ends_with_needs_you`,
   `test_status_places_each_change_under_its_board_column`, the status half of step 2's test. Green:
   `print_status()`.
5. **Readers follow (R12).** Red: `test_nothing_names_a_retired_status_section`. Green: skills,
   REFERENCE.md, AGENTS.md.

## Tests

- R1: `test_the_column_rule_is_sdlcs_alone` (board.py has no `def column`/`BY_STAGE`; `_entry`'s
  column is `sdlc.column`'s).
- R2: the existing hand-built Building/Ready tests in `test_board.py` (none call the old names).
- R3: `test_factory_land_steps_match_the_boards_track`; the problem text in R4's test.
- R4: `test_the_board_and_status_read_a_landing_in_flight_alike` (ship, gate, wait, stop, eject at `test`).
- R5: `test_status_records_only_gain_keys`.
- R6: `test_status_prints_the_board_states_in_order`.
- R7: `test_status_lists_a_change_closing_or_rebasing_under_landing`.
- R8: `test_status_ends_with_needs_you`, `test_status_says_nothing_needs_me_when_nothing_does`.
- R9: `test_status_places_each_change_under_its_board_column`.
- R10: `test_status_never_loads_the_board`.
- R11: `tests/test_next_up.py`, `tests/test_release.py`, `tests/test_push.py` unchanged and green.
- R12: `test_nothing_names_a_retired_status_section`.

## Rollback

`git revert` undoes it all: `status` writes nothing, and nothing outside the repo is created. A
host skill or script that parsed the new headings would need the old ones back; none ships.
