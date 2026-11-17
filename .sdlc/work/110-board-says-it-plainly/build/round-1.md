All six board fixes from the intent are built and the full gate passes (2201 tests). The work is left uncommitted for `/sdlc:ship`. The column head has only been checked by a test that reads its CSS. I couldn't open a browser here, so nobody has looked at it at 1280px or at phone width yet.

**Plan:** I wrote `plan.md` after reading the code. Tier 1 doesn't require one, but this change touches several files.

**Slices built, each test seen failing first:**
1. **Unreadable stop record (69):** the board now reads a broken `runs/stopped.md` the way `/sdlc:status` does, following the intent's Approach. The card shows a stop with `next: read runs/stopped.md` and `needs: stopped: read runs/stopped.md`, and no problem line. It also catches an `OSError` the same way `status` does, and `_stopped()` drops its now-unused `problems` parameter. 086's test `test_an_unreadable_stop_record_is_a_problem` becomes `test_an_unreadable_stop_record_is_a_stop_as_in_status`, which compares the card directly with what `status` reads (`sdlc.factory_stop()`).
2. **Next step follows `needs you:` (57, 70):** `next_action()` reads the `decide D<n>` items the card's `needs` already holds, so the rules stay in one place (`sdlc.needs_of()`):
   - At `build`: `decide D1 in the factory's supervisor`. This replaces "answer its decision in the factory's supervisor".
   - At `build` with a problem too: `decide D1 in the factory's supervisor, and fix what its problems name`.
   - An escalation at `test`: `decide D2, then /sdlc:ship, or /sdlc-factory:land with the others ready`.
   - Tests: `PRECEDENCE` gains `needs` and a new "escalation pending" state. A new `BOTH` map pins the two combined pairs. Two card-level tests run on real folders. 098's check on card 004, which has a problem and a blocking decision, moves to the new wording.
3. **Rebasing card (58):** the step now ends "…`--abort`, which keeps the resolved work under `refs/sdlc/end/<branch>`". Both tests that quote this text are updated.
4. **The page (52, 56):** `.col-head` is now a two-row grid, CSS only. The heading and count share the first row and the subtitle sits under the heading at every width. An empty column says "nothing waiting here" instead of "—". Two tests read the page's CSS and script to pin this.

**Outside the plan:** I updated the board section of `docs/REFERENCE.md` to match the rebasing wording, the next step following `needs you:`, and the stop reading. `plan.md` now lists this, and also records that `tests/test_sdlc.py` didn't need an edit because `status`'s side was already pinned.

Nothing went into `notes.md`. I raised no decisions, because the Approach settles the one open question: an unreadable record reads the way `status` reads it.

## Evidence

```
$ uv run --group dev pytest -q tests/test_board.py -k unreadable_stop      (before the fix)
E       assert None == {'way': None, 'next': 'read runs/stopped.md', 'problems': ["runs/stopped.md doesn't open with STOPPED: and its NEXT: line"]}
1 failed, 125 deselected in 5.85s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py -k "two_states or names_both or names_the_decision or rebased or blocking_decision or factory_signal"      (before the fix)
FAILED tests/test_board.py::test_a_card_with_a_problem_and_a_decision_names_both
FAILED tests/test_board.py::test_an_escalation_names_the_decision_it_still_needs_first
FAILED tests/test_board.py::test_a_change_being_rebased_keeps_its_card - Asse...
24 failed, 34 passed, 13 skipped, 68 deselected in 2.08s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py -k "subtitle_sits or empty_column"      (before the fix)
FAILED tests/test_board.py::test_a_column_subtitle_sits_under_its_heading - A...
FAILED tests/test_board.py::test_an_empty_column_says_so - assert 'h("div", {...
2 failed, 139 deselected in 0.18s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py
128 passed, 13 skipped in 101.45s (0:01:41)
exit: 0

$ ./check.sh
All checks passed!
2201 passed, 13 skipped in 119.51s (0:01:59)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_board.py -k "stop or two_states or names_both or names_the_decision or rebased or subtitle or empty_column or blocking_decision"
63 passed, 13 skipped, 65 deselected in 32.10s
exit: 0
```
