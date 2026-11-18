- KEPT: code: C1: scripts/sdlc.py:4482: `factory_land_stop()` returns None for `STEP: eject`, but the factory writes that step for an ejected change and the board's `LAND_STOPS` counts it as stopped. `status` and the board therefore disagree. Accept `("stop", "eject")`, update the docstring, add a `needs_of` test for an eject record, and have the pinning test state that the two stop sets agree.

## Notes
I read `factory_land_stop`, `FACTORY_STEP_RE`, `board.py`'s `LAND_STOPS` and the factory's `_record_land` and `after` handling (factory.py:2114 and 5917). I read the diff to confirm `factory_land_stop` is added in this change. I ran no tests.

The script said `code: C1` isn't a change of land-3. The prompt numbered the one change `C1`, and `reviews/land-3/code.md` holds exactly one `- CHANGE:` line, so I reused that id. My first reply also opened with a stray line ("Regex matches "eject".") before the answer, which may be what the script couldn't read. If the id is still refused, the script's numbering of this round differs from the prompt's, and its id for this change is what would settle it.
