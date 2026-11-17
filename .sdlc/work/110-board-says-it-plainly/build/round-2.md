I addressed the one kept change from round 1. The board's `_stopped()` now just calls `sdlc.factory_stop()` instead of keeping its own copy of the stop-record reader. The full gate still passes (2201 tests).

- **code: scripts/board.py:362:** `_stopped(folder)` now returns `sdlc.factory_stop(folder)`. The board and `status` now read `runs/stopped.md` with the same function, so they can't drift apart. I deleted the board's `STOPPED_RE`, `NEXT_RE` and `PROBLEM_RE`, since nothing else read them. `STOPPED` stays because `_progress()` still uses it.
  - `test_an_unreadable_stop_record_is_a_stop_as_in_status` still checks the card's stop against `sdlc.factory_stop(folder)`. That check now confirms the two are wired together.
  - `test_the_factory_parsing_is_a_pinned_copy` no longer lists the three deleted names, since there's nothing left to compare. `sdlc.py`'s own copies of those patterns are still checked against `factory.py` in `tests/test_metrics.py`.
  - The module docstring now says the stop record is read by `sdlc.factory_stop()`. Before, it implied the board read it with its own copied parsing.

**`plan.md`:** the `board.py` line, the tests line and the "Reused, not re-derived" line now describe the delegation and the dropped copies. They also note that round 1 is where the duplicate reader was found.

Nothing new is in `notes.md`, and I raised no decisions.

## Evidence

```
$ uv run --group dev pytest -q tests/test_board.py -k "stop or pinned_copy"
17 passed, 124 deselected in 3.25s
exit: 0

$ ./check.sh
All checks passed!
2201 passed, 13 skipped in 99.23s (0:01:39)
✔ Validation passed
✔ Validation passed
exit: 0
```
