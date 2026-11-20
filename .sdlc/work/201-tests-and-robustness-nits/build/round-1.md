All 29 nits are dealt with, and the full gate passed: 3557 passed, 29 skipped. The work is uncommitted, as required.

Twenty of the 29 were already fixed by change 191. Its landing retired only 5 of the 26 nits it took in, so those 20 stayed open in the register. I checked each against the current code and none needed an edit; `notes.md` names the test that settles each one. The other nine needed work.

**Slices built**
1. **`scripts/retro.py`**
   - **-33:** a hand-edited rating cell can no longer give a rating the question never offered. The nit expected a crash on a non-numeric cell, but that already read back as no rating. The real problem was that `7` read back as 7 and `2.5` as 2. Now only a whole 1 to 4 counts, and anything else is no rating.
   - **-32:** the "—" for a missing rating is now written through the existing `_num()` helper instead of relying on `_table()`. The output is unchanged, so no test can fail on this one; the existing "—" assertions cover the output.
2. **`tests/uv_run.py` (-16):** the offline-skip match now looks only for uv's own phrases, not the bare words "offline" or "no solution found". A new test fails if a script's own error message causes a skip. It first showed up as a skip rather than a failure, so the test now turns a skip into a failure.
3. **Tests:**
   - **-10:** the chained test (now in `test_factory_decisions.py`, since `test_factory.py` was split) is now two tests, one parametrized.
   - **-22:** two tests in `test_evidence_headings.py` cover each side of the blank-line rule.
   - **-26:** the insights "off" check is stronger.
   - **-34:** an unused `tmp_path` is dropped.
4. **`tests/test_train.py`:**
   - **-29:** a path staged as kept is not treated as a deletion.
   - **-30:** a moved file the resolution deleted is refused, never carried. The fallback the nit worried about can't be reached through the command, and the test pins that.
5. **Guard (new `tests/test_suite_shape.py`):** fails any test that asks for one of pytest's own fixtures (`tmp_path`, `capsys`, `monkeypatch` and similar) without using it. It found 30 more across 13 test files, and I removed the unused argument from each.

**Tests added and what they prove.** I watched each one fail first: the guard and the read-back test against the code as it was, and the rest against a deliberately broken copy, one break at a time. The copies were restored and `git diff` shows the factory scripts untouched.
- `test_a_hand_edited_rating_reads_back_as_none`: only a whole 1 to 4 is a rating.
- `test_a_script_saying_offline_is_its_own_failure`: a script's own words never cause a skip.
- `test_a_decision_reworded_with_the_same_alternatives_lands_once` and `test_a_decision_raised_again_otherwise_is_another`: each case on its own; each fails alone when its own matching rule (source, kind or options) is removed.
- `test_a_blank_line_and_a_heading_end_a_command_owing_its_exit` and `test_a_heading_with_no_blank_before_it_is_output`: the blank-line rule, each side.
- `test_config_reports_the_insights_doc`: no warning for the missing insights doc while the missing process doc does warn, and the questions are the guide's own.
- `test_a_path_staged_as_kept_is_no_deletion` and `test_a_moved_file_the_resolution_deleted_is_not_carried`: each fails when its guard is broken.
- `test_no_test_takes_a_fixture_it_never_uses` and `test_the_check_finds_a_fixture_never_used`: the guard, and a check that it finds an unused fixture.

**Named tests run:** the new and changed tests above, plus the existing `test_an_uncached_script_skips_however_uv_words_it`: 29 passed.

**`plan.md`:** written before the code. The build matches it.

**`notes.md`:** a line for each of the 20 nits 191 had settled, how each of the nine new ones was handled, and the guard.

- DECISION: [default] Make the guard the unused-fixture check? Going ahead with it.
  - OPTION: unused built-in fixture — catches the commonest kind of tests nit a script can judge; it doesn't catch weak assertions
  - OPTION: a docstring on every test helper — the kind -7 is; 431 helpers lack one today, so it would mean a huge change
  - OPTION: none, weak assertions only — those are the commonest tests nit overall, but only a reviewer can judge them
  - WHY: the intent asks for one helper or fixture against the commonest kind, and this is the commonest kind the gate can hold

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_suite_shape.py tests/test_evidence_headings.py "tests/test_retro.py::test_a_hand_edited_rating_reads_back_as_none" "tests/test_retro.py::test_a_rating_with_no_line_says_so" "tests/test_retro.py::test_config_reports_the_insights_doc" "tests/test_factory_decisions.py::test_a_decision_reworded_with_the_same_alternatives_lands_once" "tests/test_factory_decisions.py::test_a_decision_raised_again_otherwise_is_another" "tests/test_adoption.py::test_a_script_saying_offline_is_its_own_failure" "tests/test_adoption.py::test_an_uncached_script_skips_however_uv_words_it" "tests/test_train.py::test_a_path_staged_as_kept_is_no_deletion" "tests/test_train.py::test_a_moved_file_the_resolution_deleted_is_not_carried"
29 passed in 52.91s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 201 > /tmp/check201.log 2>&1
All checks passed!
3557 passed, 29 skipped in 318.60s (0:05:18)
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_suite_shape.py
E         test_acceptance.py: test_check_strict_reports_them: capsys
1 failed, 1 passed in 0.40s
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py -k "hand_edited_rating or rating_with_no_line"
FAILED tests/test_retro.py::test_a_hand_edited_rating_reads_back_as_none[7]
FAILED tests/test_retro.py::test_a_hand_edited_rating_reads_back_as_none[0]
FAILED tests/test_retro.py::test_a_hand_edited_rating_reads_back_as_none[2.5]
3 failed, 4 passed, 280 deselected in 0.62s
exit: 1

$ uv run --group dev pytest -q tests/test_adoption.py -k "offline_is_its_own"
FAILED tests/test_adoption.py::test_a_script_saying_offline_is_its_own_failure[offline]
FAILED tests/test_adoption.py::test_a_script_saying_offline_is_its_own_failure[no-solution]
2 failed, 18 deselected in 0.16s
exit: 1

$ uv run --group dev pytest -q tests/test_train.py -k "staged_as_kept or resolution_deleted_is_not"
FAILED tests/test_train.py::test_a_moved_file_the_resolution_deleted_is_not_carried
1 failed, 1 passed, 158 deselected in 12.54s
exit: 1

The last run is the red run against the second broken guard, the `is_file()` filter dropped from `deleted_sides()`. Against the first, `- set(stages)` dropped, only `test_a_path_staged_as_kept_is_no_deletion` failed.
