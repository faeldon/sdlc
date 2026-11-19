Close now measures `elapsed` from local midnight of the `created:` day, so it can't go negative. The change is uncommitted in the worktree for `/sdlc:ship`. The four close-output cases that ejected 187 now pass with their clock and timezone pinned, and I watched them fail against the old `closing.py`.

## Slices built

Tier 1 touching two files, so no `plan.md`.

1. **The fix.** `scripts/closing.py`'s `from_history` now gets its start time from a new top-level helper, `_day_start(created, now)`. It takes local midnight of `created`, with UTC midnight as a fallback if the platform can't place the date, and never lets the start fall after now. I made it a separate function because putting the logic inline pushed `measure_change` to 107 lines, which broke `test_modules.py::test_close_is_a_sequence_of_named_steps` (limit is 100). Closes measured from transcripts are untouched, and `metrics.py`'s trailer contract is unchanged.
2. **The new test.** `test_elapsed_counts_from_the_local_day_never_negative` sets the timezone to UTC+8 using a new `east` fixture (`TZ=UTC-8` plus `time.tzset()`, put back afterwards). It sets close's clock to 2026-09-30 18:00 UTC, which is 02:00 local on the `created: 2026-10-01` day. It asserts the elapsed time is exactly 2 hours and that the trailer reads `elapsed=120`. Against the old code it got −21600 s, the bug itself.
3. **The pinned close-output test.** `test_close_output_is_unchanged` now uses the `east` fixture and a new `_pin_clock()`. That fixes every clock a close reads inside the bad window: `new`'s `created:` day, its `opened:` stamp, git's author and committer dates, and close's `now`. Run against the old `closing.py`, exactly the four cases from 2026-11-20 failed (shipped, dropped, rerun, pushed) and `check` passed. With the fix all five pass. `tests/fixtures/close-output.json` needed no change.

`tests/test_archive.py` has no `portable` tests, so `time.tzset` never runs on CI's Windows job.

Nothing left in `notes.md`.

- DECISION: [default] Keep `new` stamping `created:` as the local day (the intent's open question). Going ahead with local unless told otherwise.
  - OPTION: local day, measured from local midnight — what a host's dates mean today; this fix makes elapsed correct with no change to `new`
  - OPTION: stamp `created:` in UTC — every date in the record on one clock; changes what an intent's date means for every host, and older intents would mix the two
  - WHY: the intent's Approach fixes the measurement rather than the stamp, and changing the stamp would change what a host's dates mean.

## Evidence

$ cp scripts/closing.py /tmp/closing188.py && git show HEAD:scripts/closing.py > scripts/closing.py && uv run --group dev pytest -q tests/test_archive.py -k "close_output_is_unchanged or local_day"   # old closing.py, new tests
FAILED tests/test_archive.py::test_elapsed_counts_from_the_local_day_never_negative
FAILED tests/test_archive.py::test_close_output_is_unchanged[shipped] - asser...
FAILED tests/test_archive.py::test_close_output_is_unchanged[dropped] - asser...
FAILED tests/test_archive.py::test_close_output_is_unchanged[rerun] - assert ...
FAILED tests/test_archive.py::test_close_output_is_unchanged[pushed] - assert...
5 failed, 1 passed, 164 deselected in 4.44s
exit: 1

$ uv run --group dev pytest -q tests/test_archive.py::test_elapsed_counts_from_the_local_day_never_negative   # before the fix
E       assert -21600.0 == (2 * 3600)
1 failed in 1.16s
exit: 1

$ uv run --group dev ruff check scripts/closing.py tests/test_archive.py
All checks passed!
exit: 0

$ uv run --group dev pytest -q -n 4 tests/test_archive.py tests/test_modules.py tests/test_windows.py
243 passed in 24.58s
exit: 0

$ uv run --group dev pytest -q tests/test_archive.py -k "close_output_is_unchanged or local_day"
6 passed, 164 deselected in 4.40s
exit: 0
