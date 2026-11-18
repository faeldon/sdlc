I built all 27 requirements of 145, test first, and the full gate (`./check.sh`) passes: 2749 tests passed, 28 skipped. Everything is left uncommitted in the worktree; `HEAD` is still `0710451`.

## Plan

I wrote `plan.md` after reading `board.py`, the relevant parts of `sdlc.py` and `factory.py`, the decide skill, the approver and the tests. It has an "As built" note on where the build departs from the plan:
- **Board copies:** the board gets `reasons` and `looks` from `sdlc.factory_reading()` rather than keeping a third copy of that parsing.
- **Decide skill:** it never writes `sdlc.py gate`. The existing `test_gate_is_never_pre_approved` forbids that command in any skill, so the skill points the person to the hand gate through the command `ask` gives in `then`.

## What was built, by slice

1. **Reasons in the factory (R1–R6).**
   - `escalation_reasons()` reads only the current `decision.md`. An unknown word reads as a look.
   - The ledger patterns accept a third kind, `look`, in all three copies.
   - `decisions` files each look reason once per round and text. After a restart, the old look line is history: it is never open and never asked.
   - The approver can't settle a look line, the landing's yes never ticks one, and it is never an upgrade answer.
   - `approver.md` now says every reason is a line of its own, `- ESCALATED: gate:` or `look:`.
2. **`ask` and `decide` (R11, R12).**
   - `ask` lists look items (their reply is `decision.md`) and prints a `gate` block saying whether each gate reason is cleared.
   - A look answer never sends the change back for a rebuild. With only an uncleared gate reason left, `ask --answered` says the hand gate is next.
   - The decide skill asks each look with two answers, `seen` or `checked something`.
3. **Status and needs (R7–R10, R14).**
   - `needs_of()` adds `acknowledge D<n>` and `gate it green`. `read the escalation` keeps its old rule, and also shows when a look reason isn't filed yet.
   - `sdlc.py gate` now gates a factory run at `stage: test`, and only there. Status and the board read that record for it.
   - The intent's own test passes: an escalation with a red gate goes to Ready and leaves `■ What needs me` after a green hand gate, then returns to Needs you after an edit.
4. **The landing question (R13).** `land-check` still signals `the approver escalated`, and its question now shows an `Escalated` block saying how each reason was cleared.
5. **Columns (R15–R18).**
   - The board now has six columns: Planned, Designing, Building, Ready, Landing and Needs you.
   - A change built by hand is never Ready while its hand gate is current and red.
   - I updated `board.html`, REFERENCE.md (the three places), the AGENTS.md board paragraph and the factory README, and moved every old column assertion to the new names.
6. **A landing's progress (R19–R24, R26).**
   - Each landing step's time goes into `runs/land-times.jsonl` when the next step replaces it, and the board takes typical times from closed changes' copies.
   - Open-ended steps (`resolve`, `fix`, `mend`, `cases`, `wait`) and steps with no history show elapsed time and `running`, never a bar.
   - As the train turns to a change, each committed change behind it records `wait` with `WAITS: stack on …` or `close after …`. The card reads `waiting to stack on 140`.
   - `accept` after the commit records `recheck`, which sits on its own track position between gate and review.
7. **Folded-in seeds (R25, R27).**
   - A landing mid-rebase whose builder is resolving the conflict now says to wait for it, instead of giving the hand-run `sdlc.py resolve` line.
   - The "doesn't open with" messages now say the reply holds no answer the script reads, and the board's copies are pinned to the factory's.

## Tests added
- **`test_factory.py`:**
  - R2: `test_escalation_reasons_read_the_current_decision_alone`.
  - R3: `test_a_look_reason_is_filed_once`, `…_filed_again_after_a_restart`.
  - R4: `test_a_look_line_is_counted_in_no_ledger_figure`.
  - R5: `test_only_the_person_ticks_a_look_line`.
  - R6: `test_a_restart_makes_a_look_line_history`.
  - R11: `test_ask_lists_look_items_and_the_gate`, `test_ask_says_ship_once_a_look_is_seen_and_no_gate_is_owed`.
- **`test_sdlc.py`:** R9 `test_needs_of_an_escalation_by_its_reasons`, a 12-case table.
- **`test_hand_gate.py`:** R7 `…gates_a_factory_run_at_test_alone`, `…counted_in_no_factory_figure`; `test_the_factorys_hand_build_is_sdlcs` pins the factory's copy of the hand gate to `sdlc.py`'s.
- **`test_board.py`:**
  - R8 and R10, the intent's test: `test_a_green_hand_gate_clears_a_gate_reason_until_an_edit`.
  - R9 on the board: `test_a_look_is_acknowledged_and_clears`.
  - R7: `test_a_hand_gate_record_is_no_land_gate_sample`.
  - R15: `test_hand_and_factory_changes_share_a_column_per_state` (five states), `test_a_factory_landing_is_landing_before_and_after_its_commit`, `test_a_restart_cut_short_at_test_is_building`.
  - R16: `test_a_hand_change_is_ready_by_review_or_a_green_gate_never_a_red_one`.
  - R17: `test_the_columns_name_the_state_of_the_work`; the new `PRECEDENCE`/`BOTH` pairs (look to acknowledge, gate reason owed, landing conflict).
  - R20: `test_landing_step_times_come_from_land_times`.
  - R21: `test_an_open_ended_step_never_shows_a_fraction`.
  - R23: `test_a_train_of_three_shows_its_step_place_and_wait`.
  - R24: `test_the_land_record_readers_are_pinned_copies`, over the new `tests/fixtures/land-record-cases.json`.
  - R25: the landing-conflict line, added to an existing rebase test.
  - R26: `test_a_recheck_after_the_commit_sits_after_the_gate`.
  - R27: `test_the_boards_problem_words_are_the_factorys`.
- **`test_land.py`:** R13 and R10 `test_land_check_shows_how_each_reason_was_cleared`; R19 `test_each_landing_step_change_writes_a_times_row`; R26's post-commit `recheck`.
- **`test_train.py`:** R22 `test_a_waiting_change_records_what_it_waits_on`.
- **`test_metrics.py`:** R14 `test_a_cleared_escalation_still_measures_as_escalate`; the new copies pinned (`REASON_RE`, `LOOK_SOURCE_RE`, `factory_reasons()`, `factory_newest_round()`).
- **`test_skills.py`:** R1 and R12 wording tests.

The R14 test and the R6 test passed as soon as they were written, because the code they check already existed: they guard the behaviour rather than drive it. R10 is proved across two tests: the board test checks the board and the hand gate leave `decision.md` alone, and the land test checks `decisions`, `ask`, `sdlc.py gate` and `land-check`. No single test runs all five.

`notes.md`: nothing left.

- DECISION: [default] Write one `Escalated` line per `gate` reason in the spec's exact words (`gate: green on the build as it stands (attempt N)` / `gate: not cleared`), without the reason's own text. Going ahead unless told otherwise.
  - OPTION: spec's words only — matches R13 exactly; two gate reasons show as two identical lines
  - OPTION: add the reason's text (`gate (<why>): …`) — tells reasons apart; departs from R13's wording
  - WHY: R13 gives the line forms word for word, and one green hand gate clears every gate reason at once anyway
- DECISION: [default] A train writes `wait` only for changes already committed, after the one it acts on, and never over a `stop` or `eject` record or a change mid-rebase. Going ahead unless told otherwise.
  - OPTION: committed changes only — the record is amended into the change's own commit like the rest; nothing dirties a branch before its commit exists
  - OPTION: every live change behind — waiting shows even during the commit step; the record would ride into the change's commit without being one of its landing records
  - WHY: `_amend_record()` needs the landing's commit to amend into, and `resolve --onto` amends dirty records first

## Evidence

$ uv run --group dev pytest -q tests/test_factory.py -k "escalation_reasons or look or ask_lists_look"
7 failed, 330 deselected in 8.16s
exit: 1

$ uv run --group dev pytest -q tests/test_sdlc.py -k by_its_reasons
7 failed, 5 passed, 250 deselected in 0.30s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py -k "share_a_column or landing_before or cut_short or by_review_or or name_the_state"
9 failed, 228 deselected in 2.79s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py -k "land_times or open_ended or train_of_three or record_readers or recheck or landing_track"
20 failed, 1 passed, 272 deselected in 2.67s
exit: 1

$ uv run --group dev pytest -q tests/test_train.py -k "waits_on"
1 failed, 23 deselected in 4.13s
exit: 1

$ uv run --group dev pytest -q tests/test_train.py -k "waits_on"
1 passed, 23 deselected in 10.69s
exit: 0

$ uv run --group dev pytest -q tests/test_land.py -k "records_each_step_it_takes"
1 passed, 75 deselected in 7.95s
exit: 0

$ ./check.sh
All checks passed!
281 files already formatted
2749 passed, 28 skipped in 200.49s (0:03:20)
✔ Validation passed
✔ Validation passed
exit: 0

$ git log --oneline -1
0710451 Close 141-board-landing-track-truth
