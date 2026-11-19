I re-recorded `tests/fixtures/close-output.json` on the new main. That file is the only one I changed, and the full gate passes: 3156 passed, 29 skipped, exit 0.

The only new thing in the copies is one trailer, `Sdlc-Runtime: plugin=1.10.0`. In each of the five scenarios it is now the last line of the report's `measure.trailers`, and the last trailer on each commit close wrote (the shipped, dropped and pushed `Close`/`Drop` commits and the rerun's `Close`). The failed first run of the rerun scenario has it in its report only, since that run wrote no commit. Nothing else changed: no report key, step name, exit code or tree. In these five scenarios, 169 and 170 together add just that line; any other trailer they write doesn't come up here.

I recorded it the same way as the first time: a temporary test file running each scenario through the test's own `_close_scenario()`. I deleted it straight after, and the old fixture was saved to `/tmp/rec172/` for the comparison. `closing.py`, the test and its normaliser are untouched, so the move is unchanged. I ran no git command.

- DECISION: [default] Leave the plugin version pinned in `close-output.json`? Going ahead with it pinned, as asked.
  - OPTION: leave it pinned — the copies are exactly what close writes; but the next version bump in `plugin.json` makes `test_close_output_is_unchanged` fail until someone re-records it
  - OPTION: add `Sdlc-Runtime`'s `plugin=` value to what `_normal()` blanks out — survives every release; one more line in the test, which this fix wasn't asked to touch
  - WHY: the request was to re-record only. The second option is worth doing before 1.10.0 is bumped.

## Evidence

$ uv run --group dev pytest -q tests/test_archive.py::test_close_output_is_unchanged   (old fixture, new main)
4 failed, 1 passed in 5.37s
exit: 1

$ uv run --group dev pytest -q -p no:randomly tests/test_zz_record172.py   (one-off recorder, deleted after)
5 passed in 4.81s
exit: 0

$ diff <old fixture, flattened> <new fixture, flattened>
`Sdlc-Runtime: plugin=1.10.0` added to the end of each run's `measure.trailers` (shipped, dropped, check-free rerun ×2, pushed) and to each commit close wrote (shipped, dropped, rerun 2nd run, pushed); no other line differs
exit: 1

$ uv run --group dev pytest -q tests/test_archive.py::test_close_output_is_unchanged
5 passed in 4.69s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 172
All checks passed!
325 files already formatted
3156 passed, 29 skipped in 171.23s (0:02:51)
✔ Validation passed
exit: 0
