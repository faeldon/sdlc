VERDICT: CHANGES
- CHANGE: scripts/board.py:362: `_stopped()` re-implements `sdlc.factory_stop()` (the same read, the same `OSError` branch, the same three parsing regexes at lines 62–64, and the same `problems` wording). The plan says "Reused, not re-derived: `factory_stop()`'s wording", and the board already calls `sdlc.needs_of()` so the two surfaces can't drift. Make it `_stopped(folder)` return `sdlc.factory_stop(folder)` (or call it from `_entry` directly), then delete `STOPPED_RE`, `NEXT_RE` and `PROBLEM_RE` from board.py, since nothing else reads them. The existing equality assertion in `test_an_unreadable_stop_record_is_a_stop_as_in_status` still holds and now pins the wiring.

## Notes

What is done well: the pass-through of `needs` into `next_action()` keeps the rule in one place (`needs_of`), and the escalation and problem-plus-decision cases have card-level tests on real folders, not only the `PRECEDENCE` table. The `refs/sdlc/end/<branch>` clause is accurate: `cmd_resolve`'s abort path reads `ref["end"]`, which `finish()` writes.

- Not verified visually. The `.col-head` test only checks the CSS text (grid, `1fr auto`, `.who` on row 2), and the builder could not open a browser. Before ship, check the board at 1280px and at phone width, as plan.md's manual step says.
- Stop plus pending decision at `build`: `next_action()` names only the stop (`read runs/stopped.md`), because the stop precedes the decision in `PRECEDENCE`. The decision is still on the `needs you:` line. That follows the stated precedence, so I don't count it as a change, but the card does not say a decision waits too, as 57 asks for problems. Worth a deliberate choice; it is not a finding.
- `status`'s side has no end-to-end test of a garbled `runs/stopped.md`. `test_a_stop_needs_its_way_on` pins `needs_of` with `way: None`, and the board test compares with `factory_stop` directly, so the shared function is covered. The intent's "tests/test_sdlc.py for status" was dropped in plan.md, which is acceptable once the first change lands.
- `_stopped`'s docstring says "a test pins the two"; after the CHANGE above, reword it to say the card returns `factory_stop`'s reading.

Tests run: `uv run --group dev pytest -q -n auto tests/test_board.py` gave 128 passed and 13 skipped. `ruff check` and `ruff format --check` on `scripts/board.py` and `tests/test_board.py` were clean. I did not rerun the full `./check.sh`; the builder's gate record shows 2201 passed.
