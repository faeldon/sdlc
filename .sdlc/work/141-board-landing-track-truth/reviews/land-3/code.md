VERDICT: CHANGES

- CHANGE: [contract] scripts/sdlc.py:4482: `factory_land_stop()` accepts only `STEP: stop`, but 139's train now writes `STEP: eject` through `_record_land(..., "eject", ...)` (factory.py:5917). The board's `LAND_STOPS = ("stop", "eject")` shows such a change as stopped and puts it in Needs you. `status` shows "nothing" for the same change. That breaks the rule `needs_of()` states, that the board and `status` can't disagree. It is also a combination only this rebase creates, so it belongs in this change and not in a follow-up. The fix is to accept `step.group(1) in ("stop", "eject")` and update the docstring. `after` already comes from the record's `AFTER:` line, which factory.py:2114 writes for an eject. Add a test in `tests/test_sdlc.py` that a `land-step.md` with `STEP: eject` gives `needs_of` "landing stopped at …". Also state in the board/factory pinning test that the two stop sets agree.

## Notes
- The builder's DECISION [default] to file the `eject` gap as a follow-up is overridden. The fix is two lines in a file that the change's own diff already edits, and leaving it open ships a disagreement the change exists to remove. In the next landing round, the builder should be allowed to edit `sdlc.py`.
- Otherwise the rebase resolution is sound. `LAND_STEPS`, `LAND_AT` and `LAND_LABEL` hold both sides' entries. `_land_refused` calls both the plain-line recorder and `_train_fail()`. No conflict markers remain.
- I ran no tests. I rely on the builder's evidence of a green `./check.sh`, and I read the diff of `sdlc.py` and `board.py`.
- NIT: scripts/board.py:100: the eject-at-gate default is explained only in the comment above; a test that pins `LAND_AT["eject"]` to the gate position would catch drift {tests S low}
