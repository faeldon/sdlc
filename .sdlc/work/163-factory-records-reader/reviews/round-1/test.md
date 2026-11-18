VERDICT: PASS

I mapped each requirement to its test in the diff, and the gate's record shows a green run. I ran no tests myself.

## Notes
- **R1:** `test_factory_records_is_pure_and_loaded_once` checks for a single load site in `sdlc.py`, no `subprocess`, `sdlc` or `importlib` in the module, and no script named outside docstrings. It also checks that the module only defines names at load. It would fail on a second load site or a bound `sdlc`.
- **R2:** `test_the_board_and_close_read_records_through_sdlc` asserts that `board.py` and `closing.py` do not load the module, and that `sdlc.factory_records` is the same object in the board and in close.
- **R3, R4:** `test_the_record_readers_live_in_factory_records` uses `RECORD_NAMES`, `OLD_NAMES` and `CONSUMER_NAMES`, and checks that the module holds none of the consumers.
- **R5:** `test_no_factory_record_is_named_outside_its_reader` runs its checker on a snippet first, so it is shown to fail. It also checks that docstring and prose cases are not caught.
- **R6:** `test_every_shared_name_is_the_factorys` pins every name the two modules share, flags included. It sanity-checks that `LEDGER_RE`, `STOPPED`, `LAND_STEPS`, `NO_DECISION` and `REVIEWERS` are among the shared names.
- **R7:** the pins now read `sdlc.factory_records`. The two `opening` tests were merged into the board's test over `opening-cases.json`, and the old metrics test was removed. The merged test compares the module's `opening` with the factory's over the same cases. `read_step`, `cost`, `reasons`, `newest_round`, and `placeholders` with `DEFUSE` are all pinned too.
- **R8:** the other test diffs are renamed reads and reformatted lines. I saw no changed expected value in the diff.
- **R9:** `tests/test_archive.py` is untouched, and so is the `_factory_files` test in `test_metrics.py`, so the adapter signatures are checked as the spec asks.
- **Gate record, `build/round-1.gate.md`:** exit 0, ruff clean, plugin validation passed, and `2964 passed, 28 skipped`.
- **`checks.md`:** there is none for this change, and none is needed.
- NIT: tests/test_modules.py: a few helper names such as `_reached` and `_named` have no docstring {tests S low}
