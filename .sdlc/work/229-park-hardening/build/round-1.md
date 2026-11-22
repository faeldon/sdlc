I built all six fixes from the intent. The named tests now pass (927 passed, 28 skipped) and ruff is clean. The one full gate run I did had a single failure: AGENTS.md went past 100 columns. I fixed that and reran that test, which passed, but I haven't rerun the full gate since; the factory's own gate will run it next.

## Slices built
`plan.md` is written. The intent is Tier 1, but its Approach touches five files, so it needed one.

1. **`[park] exit` refuses 0 and 1.** `_park()` now only takes a code from 2 to 255. A 0 or 1 gets the same treatment as any other bad value: a warning that names 75 (EX_TEMPFAIL) as the one to use, and nothing parks. The factory README's `[park]` block, `docs/REFERENCE.md` and the docstring say the same.
2. **`busy_of()` drops control characters.** `clean()` folds whitespace first, then removes every C0 and C1 control character (`CONTROL_RE`). This happens before the value is marked and cut to 200 characters.
3. **`park --clear` removes an unvouched record whatever its deadline.** `verdicts` never treats such a record as a park, so `--clear` now removes it instead of refusing. It still refuses a real park before its deadline.
4. **The slot-wait test now checks the wording.** It asserts `no gate slot came free` as well as `didn't run`. The code already printed that wording, so the stricter test passed straight away and was never red.
5. **`needs_of()` gets the capped deadline.**
   - `factory_records.py` has a new `capped_park(park, minutes)`, a copy of the factory's that a test pins to it. `park(folder, minutes)` now returns the park capped.
   - `sdlc.py` has a new `_park_deadline_at(home, trunk)`, which reads `[park] deadline` from the base branch only, as `_gate_jobs_at()` does for `gate_jobs`.
   - `status` and `board.py` both pass that value in. `needs_of()` itself is unchanged and is still the one place the rule lives.
   - The board tests' park fixture had an old start time with a far deadline. Under the cap that meant "past its deadline", so I moved its start time to 30 minutes before that deadline.
6. **AGENTS.md's Skills list names `update`.** I put it on the list's first line, which had room. Reflowing the paragraph broke `test_agents_md_fits_100_columns` in the full gate run.

## Tests added
- `test_park_exit_of_0_or_1_is_refused[0,1]`: each warns, names 75 and leaves nothing parking.
- `test_busy_payload_drops_control_characters`: ESC, BEL, DEL, NUL and the C1 CSI character are removed, and a tab becomes a space.
- `test_park_clear_removes_an_unvouched_record`: an edited record is cleared before its deadline.
- `test_both_park_caps_cut_a_record_alike[1,30,60,1440]`: core's copy of the cap matches the factory's.
- `test_the_park_deadline_is_read_as_the_factory_does`: the deadline is read from the base branch only, and every value the factory refuses gives 60.
- `test_a_park_past_the_base_branchs_deadline_needs_you`: a record with a far-off deadline of its own still shows as needing you, on the board and in `status`, once the capped deadline has passed.

`checks.md` has two checks for things only a revert could break: `update` in AGENTS.md's list, and "75 … is the one to use" in the factory README. Both passed through `sdlc.py accept`.

## In `notes.md`
- [ ] Both copies of `read_park()` take `RESOURCE:` and `HOLDER:` as written, so a hand-edited `runs/parked.md` with an ESC in it still reaches `status`. Stripping on read would cover that; it is outside this change's scope.

## Decisions
- DECISION: [default] Refuse `[park] exit = 0` and `= 1` with a warning (the value is dropped and nothing parks), rather than only warning and still parking on it. Going ahead with refusing unless told otherwise.
  - OPTION: refuse with a warning — a red check can never become a wait; a host that set 1 gets no parks until it changes the value
  - OPTION: warn only, still park — the host's value is honoured; every ordinary red gate becomes a wait, the problem the nit raised
  - WHY: the intent's Approach says refuse, and other bad `[park]` values are already handled this way.
- DECISION: [default] `park --clear` removes an unvouched record even before its recorded deadline. Going ahead unless told otherwise.
  - OPTION: remove whatever its deadline — no reader takes it as a park, so nothing real is lost
  - OPTION: remove only once expired, and name the `rm` in the refusal — keeps the old rule; the person still has to delete a record that never counted
  - WHY: `verdicts` already treats an unvouched record as a stop to rerun, never a wait.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_factory_park.py -k "0_or_1 or control_characters or unvouched or slot_wait_parks"
4 failed, 1 passed, 21 deselected in 48.74s
exit: 1

$ uv run --group dev pytest -q tests/test_factory_park.py
26 passed in 41.25s
exit: 0

$ uv run --group dev pytest -q tests/test_board.py -k "park" tests/test_modules.py::test_both_park_caps_cut_a_record_alike tests/test_hand_gate.py::test_the_park_deadline_is_read_as_the_factory_does tests/test_modules.py::test_the_record_readers_live_in_factory_records
FAILED tests/test_board.py::test_a_park_past_the_base_branchs_deadline_needs_you
FAILED tests/test_board.py::test_status_shows_a_parked_change_under_building
FAILED tests/test_modules.py::test_both_park_caps_cut_a_record_alike[1] - Att...
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_modules.py tests/test_hand_gate.py tests/test_factory_park.py
131 passed in 10.98s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 229
FAILED tests/test_feature_map.py::test_agents_md_fits_100_columns - assert [3...
1 failed, 4039 passed, 29 skipped in 528.53s (0:08:48)
exit: 1

$ uv run --group dev pytest -q tests/test_feature_map.py::test_agents_md_fits_100_columns
1 passed in 0.07s
exit: 0

$ uv run --quiet --script scripts/sdlc.py accept 229
  "passed": true,
  "problems": []
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_factory_park.py tests/test_modules.py tests/test_hand_gate.py tests/test_board.py tests/test_feature_map.py tests/test_skills.py
927 passed, 28 skipped in 51.21s
exit: 0

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
343 files already formatted
exit: 0
