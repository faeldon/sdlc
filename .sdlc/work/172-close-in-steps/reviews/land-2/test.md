VERDICT: PASS

The re-record covers the five scenarios, and the pinned test passes against it.

## Notes
- No `build/land-2.gate.md` exists yet. The gate's result for this round is only what `land-2.md` reports (3156 passed, 29 skipped, exit 0). I did not run the whole suite.
- I ran `tests/test_archive.py::test_close_output_is_unchanged` by name and got 5 passed. The fixture holds `Sdlc-Runtime: plugin=1.10.0` nine times (the lines are at 52, 69, 116, 133, 244, 306, 323, 393 and 409), which matches the builder's account.
- The test compares the whole fixture, so it fails if the move changes any report key, step name, exit code or trailer. The re-record kept the move unchanged.
- The builder's DECISION is a `[default]` one: leave the plugin version pinned in `close-output.json`. The fixture will fail on the next `plugin.json` bump until someone re-records it. I agree with going ahead as asked.
- NIT: tests/test_archive.py: blank the `plugin=` value in `_normal()` so a release bump doesn't break `test_close_output_is_unchanged` {tests S med}
- `checks.md`: this change has none.
