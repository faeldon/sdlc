I built 151: `status` now groups open changes under the board's columns and ends with `■ Needs you`. The full gate passes: `./check.sh` exits 0 with 2838 passed and 28 skipped. Nothing is committed; the work is uncommitted in the worktree for `/sdlc:ship`.

**What I built, one slice at a time, each test seen failing first:**
1. **One column rule (R1, R2).** `column()` and `BY_STAGE` moved from `board.py` into `sdlc.py` unchanged, along with `seen_stage()` (was `_seen()`), `touched_paths()` (was `_touched()`) and `rebasing_branches()` (was `_rebasing()`). The board now calls them as `sdlc.<name>`. All of `tests/test_board.py` passed after the move.
2. **A landing in flight, read once for both (R3, R4).** A new `factory_landing(folder, stage)` and a `FACTORY_LAND_STEPS` copy, pinned to the board's `LAND_AT`. The board sets `entry["in_flight"]` from it, and `column()` reads that instead of the board's own `progress`. In `status`, a garbled `runs/land-step.md` now adds the board's problem text.
3. **Status reads the column (R5, R10).** Each open record gets `column` from `column()`. Each shipped or dropped record waiting on close gets one too, with `needs` and `mode`. A new `held_by_rebase()` adds the shipped or dropped changes a stopped rebase holds.
4. **Status prints by state (R6, R7, R8, R11).** After the header come `■ Planned`, `■ Designing`, `■ Building`, `■ Ready` and `■ Landing`, each with its count; an empty one prints alone. Close lines are under Landing. `■ Needs you: N` is the last section: each change's line, then a `needs you: …` line, plus `/sdlc-factory:decide NNN` where it applies.
5. **Readers follow (R12).** I updated `skills/status/SKILL.md` (precedence step 2 is now a `→ /sdlc:close` line under Landing), `skills/close/SKILL.md`, the factory's `decide` skill, `docs/REFERENCE.md` and `AGENTS.md`'s board paragraph.

Running `status` from this worktree shows the new order, with this change (151) under Building and 149 under Needs you. The spec expected 151 under Designing, but its stage line now says `build`, so Building is correct.

**New tests, all in `tests/test_board.py`:**
- `test_the_column_rule_is_sdlcs_alone` (R1, R2): `board.py` defines none of the moved functions.
- `test_factory_land_steps_match_the_boards_track` (R3): the two step lists can't drift.
- `test_the_board_and_status_read_a_landing_in_flight_alike` (R3, R4): `ship`, `gate` and `wait` land in Landing on both sides; `stop`, `eject` and a garbled record land in Needs you on both.
- `test_status_prints_the_board_states_in_order` (R6).
- `test_status_lists_a_change_closing_or_rebasing_under_landing` (R7).
- `test_status_places_each_change_under_its_board_column` (R9): twelve changes, one hand-built and one factory at each state.
- `test_status_never_loads_the_board` (R10): keeps its old source check, and now also runs `status` with `_load_board` set to raise.
- `test_nothing_names_a_retired_status_section` (R12).

**Existing tests I changed:**
- `test_status_ends_with_what_needs_me` is now `test_status_ends_with_needs_you`, with the exact text for 004, 013 and 041. It normalises the change's age and touched time, which change with the clock.
- `…stopped_landing_under_what_needs_me` is now `…under_needs_you`.
- Three other status tests read the new headings, and `records_only_gain_keys` now expects `column`.
- `_hand_at_state()` and `_factory_at_state()` take an optional name, because "planned" and "landing" are both seven letters and made clashing change numbers.

**`plan.md`** is written, then updated to what I built: `held_by_rebase()`, `_by_state()` (a record printed without a `column` is placed by its stage), and the test renames.

**`notes.md`:** nothing added.

- DECISION: [default] Keep `■ Needs you` last, not first as the intent's Outcome says. Going ahead with last unless told otherwise.
  - OPTION: last — the board's order, the spec's call and where the eye ends; contradicts the intent's word "first"
  - OPTION: first — what the intent says; breaks the board's order, and the status skill's guidance and test would need rewriting
  - WHY: the spec decided it from the code, the board and the skill, and its "Left for you" names it as the person's call
- DECISION: [default] Leave the problems only the board reads (a reply with no VERDICT, an unreadable findings or step file) off `status`. Going ahead with leaving them off unless told otherwise.
  - OPTION: leave them off — `status` stays quick; such a change sits under its stage's state in `status` but under Needs you on the board, as REFERENCE.md now says
  - OPTION: read them all — closes the gap completely; `status` reads every review file of every change
  - WHY: the spec's Boundaries say to ask before closing this gap, and this change already closed one part of it (`runs/land-step.md`)

## Evidence

$ uv run --group dev pytest -q tests/test_board.py -k "sdlcs_alone or land_steps_match or in_flight_alike or states_in_order or closing_or_rebasing or under_its_board_column or retired_status"   (before the code: red)
FAILED tests/test_board.py::test_the_column_rule_is_sdlcs_alone - AssertionEr...
FAILED tests/test_board.py::test_factory_land_steps_match_the_boards_track - ...
FAILED tests/test_board.py::test_the_board_and_status_read_a_landing_in_flight_alike
FAILED tests/test_board.py::test_status_prints_the_board_states_in_order - As...
FAILED tests/test_board.py::test_status_lists_a_change_closing_or_rebasing_under_landing
FAILED tests/test_board.py::test_status_places_each_change_under_its_board_column
FAILED tests/test_board.py::test_nothing_names_a_retired_status_section - Ass...
7 failed, 293 deselected in 47.08s
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_bugs.py tests/test_next_up.py tests/test_release.py tests/test_push.py
199 passed in 16.57s
exit: 0

$ uv run --quiet --script scripts/sdlc.py status   (filtered to headings and change lines)
■ Planned: 1
■ Designing: 0
■ Building: 4
    151  T2 build      0d  status-by-board-states       intent plan spec  · …
■ Ready: 0
■ Landing: 0
■ Unreleased: 39
■ Next up: 18
■ Release due: 19 changes of minor impact or higher  /sdlc:release
■ Problems: 1
■ Needs you: 1
    149  T2 build      0d  landing-resolver-agent       …
                              needs you: fix: fixes: '2026-11-18-73' isn't a [bug] in .sdlc/work/inbox.md
exit: 0

$ ./check.sh
All checks passed!
280 files already formatted
2838 passed, 28 skipped in 398.75s (0:06:38)
✔ Validation passed
exit: 0
