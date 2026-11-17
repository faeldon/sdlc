VERDICT: PASS

The spec names no command for a person to run end to end, so I ran the closest path, the landing tests in `tests/test_land.py`. All 17 pass against the rebased tree, and the wider factory suite passes too. Every new test the spec names is present.

## Notes
- **`checks.md`:** the change has none, so there was nothing to read.
- **Gate record:** `build/round-1.gate.md` and `build/land-1.gate.md` both end in `✔ Validation passed`. I did not run the gate again.
- **Not run:** the factory skill cases (`preflight`'s `cases.scope`), because each run is a paid model call.
- **Rebase:** `git status` shows only two untracked files, `build/land-1.gate.md` and `runs/reviewer-behaviour.sessions`. They are this landing's own records, not stray changes.
- **Spec coverage, R1–R18:**
  - R1, R2: `test_land_close_reads_a_modified_first_path_in_the_folder_as_the_folders` and `test_a_landings_record_never_takes_in_a_path_outside_its_folder`.
  - R3, R4: `test_a_second_land_after_main_moves_rebases_with_the_first_record_amended_in` and `test_a_record_is_never_amended_into_a_commit_the_landing_didnt_make`.
  - R6–R9: `test_a_landing_retires_the_nits_its_intent_names`, the extended `test_a_refused_step_lands_nothing_of_that_change`, and `test_the_landings_nits_are_the_ones_sdlc_reads`.
  - R10–R15: `test_a_landing_resolution_counts_until_its_review_passes`, `test_a_resolution_the_build_reviewed_is_no_signal_and_one_after_it_is`, `test_the_landings_resolutions_are_the_ones_sdlc_reads` and `test_an_auto_landing_never_closes_over_a_resolution_no_review_passed`.
  - R5, R12, R16, R17: I did not check these by running anything; they are structure and skill text.

## Evidence
$ uv run --group dev pytest tests/test_land.py -q -n auto
.................                                                        [100%]
17 passed in 8.88s
exit: 0

$ grep -c "^def test_" tests/test_land.py; git status --short; uv run --group dev pytest tests/test_land.py tests/test_factory.py -q -n auto
17
?? .sdlc/work/097-landing-fixes/build/land-1.gate.md
?? .sdlc/work/097-landing-fixes/runs/reviewer-behaviour.sessions
175 passed in 8.37s
exit: 0
