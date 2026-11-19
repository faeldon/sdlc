VERDICT: PASS

Every requirement R1–R13 has a test or a sound acceptance check, and I found nothing that blocks.

## Notes

- **Gate:** `build/round-1.gate.md` is green with `3254 passed, 29 skipped`, and `claude plugin validate --strict` passes. I did not rerun the suite.
- **Tests I ran, named, in the foreground:** the retro tests for outside, restored, overrides, unknown and hand-commit, plus `tests/test_archive.py::test_measures_errors_never_become_a_trailer`. Result: `7 passed, 191 deselected`.
- **Mapping:**
  - R1: `test_a_hand_commit_on_the_base_is_outside_the_loop`, parametrised with and without the hand commit. The fixture includes register, release, setup and drop commits, which each count 0. `test_the_window_starts_after_the_repo_took_the_plugin_up` covers the adoption window.
  - R2: `test_a_hand_commit_to_a_record_is_told_from_one_to_code`.
  - R3: `test_an_entry_filed_again_after_it_was_retired_is_restored`. It also covers a new id and an edit, which count 0.
  - R4: `test_a_stopped_trains_rows_name_it`. It checks the key order `at, land, cause, train` and the same `began` in each change.
  - R5: `test_an_ejection_that_cant_be_recorded_still_ejects`. It makes `ejections.jsonl` a directory, so the append raises `OSError`. It asserts the change is ejected, the undo is printed and a problem names the file.
  - R6, R7: `test_overrides_are_read_from_each_factory_changes_commit`, `test_with_no_factory_change_the_overrides_are_null` and `test_a_change_with_no_start_leaves_its_commits_unknown`. The first covers the same-train stop counting once, `gate`/`review` by cause, rows with no `train` counting once per change, a garbled line, a dropped change's tip and a hand-built change left out of `n`.
  - R8: the new retro tests assert `_state(root)` is unchanged.
  - R10: `test_measures_errors_never_become_a_trailer`.
  - R11: `RECORD_NAMES` extended, `.ask.md` added to `RECORD_FILES`, and `test_land_ask_re_reads_the_factorys_path`, which builds the path with `factory.land_ask_path()`.
  - R13: the existing unmeasured test, extended.
  - `SETUP_SUBJECTS`: `test_setup_subjects_are_the_skills_own`.
- **Checks in `checks.md`:**
  - *The review names the doc-claim failure class (R9)* greps the `.sdlc/REVIEW.md` section for the bullet. I read the diff and the bullet is there. It fails only if the bullet is removed, it can fail, and it leaves the tree unchanged.
  - *The docs describe the workarounds (R12)* greps four docs. I checked the two fixed strings in the factory README and the scorecard, and each matches once. It also fails only on a revert and leaves the tree unchanged. I did not run either check.
- **Not covered:** nothing tests an unknown-start commit that touches a record. The code treats it as `unknown` first, so this is low risk.
- NIT: tests/test_retro.py:3704: the `unknown` rows carry a `change` key that no test asserts, and `unknown` has no `n` {tests S low}
- NIT: tests/test_retro.py:3677: add one assertion that a stop before any commit leaves no row, since the spec's edge-case section names it {tests S low}
