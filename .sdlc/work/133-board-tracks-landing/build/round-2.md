I've fixed all three kept changes, and the full gate passes (2404 passed, 14 skipped). On C1 I took a different route from the one the reviewer suggested; the reason is below and in `notes.md`. Nothing is committed.

## The kept changes

- **code C1 (a moved landing kept saying `close` with an old move count).** Fixed, but not with the suggested `stop`. When the base branch moves, `land --close` now counts the move, then writes `rebase` to `runs/land-step.md`, then amends the commit. This happens on both paths: a move found before the close, and one that races it. The card then reads "now: rebase" with the right "base moved m of k times", and the record is in the commit the amend makes.
  - Why not a `stop`: a move isn't one. The skill goes straight back to `land` without asking the person. A `stop` would mark a still-running landing as stopped, give the card the stopped look, and tell the person to "fix what it names".
  - Tests: two existing landing tests now read the record right after `moved`. They check its step is `rebase`, its move count is 1, and the commit holds the same record.
- **ux C2 (a shipped card mid-landing said `/sdlc:close`).** While a landing is under way, before or after its commit, the card's next step now reads "the factory is landing it, at <step>: wait for it, or /sdlc-factory:land <id> if its session ended". `/sdlc:close` comes back only once there is no landing record. The "Ready to close" column subtitle now reads "/sdlc:close, or the factory's landing".
  - Tests: both states are added to the next-step precedence tests, ranked above shipped's close; `test_a_landing_card_names_the_landing_not_close` checks the card.
- **ux C3 (a stopped landing looked ready, said the ready next step, and showed raw output).**
  - The card keeps its column but gets a red stop edge in place of the blue ready look.
  - Its next step says the way on: "the landing stopped at <step>: fix what it names, then /sdlc-factory:land <id>, or /sdlc:ship <id> by hand".
  - Stops caused by a tool's raw output now record plain words on the card: ship refused, the commit failed, `base` refused, the rebase failed, and a failed close. The tool's own words stay in the command's JSON output.
  - Tests: `test_a_stopped_landing_drops_the_ready_look`, `test_a_landing_stopped_by_a_tool_records_plain_words`, and the board test above.

## Other changes

- `docs/REFERENCE.md` describes the landing card's next step and how a stop looks.
- `plan.md` now covers the round 1 changes.
- `notes.md`:
  - The open item about `/sdlc:close` is gone, since C2 fixes it.
  - It now explains the C1 choice.
  - Still open: moving a stopped landing to Needs you (D5), and `accept` not recording a step.

## Evidence

$ uv run --group dev pytest -q -n auto tests/test_board.py
FAILED tests/test_board.py::test_a_card_in_two_states_names_the_higher_ones_step[landing-landing]
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_land.py
62 passed in 14.38s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_board.py
181 passed, 14 skipped in 5.57s
exit: 0

$ ./check.sh
All checks passed!
2404 passed, 14 skipped in 59.19s
✔ Validation passed
exit: 0
