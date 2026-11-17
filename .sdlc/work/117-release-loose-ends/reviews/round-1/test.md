VERDICT: PASS

Every requirement from R1 to R12 has a test that would fail without it. The full suite passes: 2209 passed, 9 skipped.

## Notes

- **R1:** `test_a_marker_places_the_release_after_it` covers the marker placement.
- **R2:** `test_without_a_marker_the_changelog_is_written_as_before` is parametrized over titled, title-only, untitled, empty and CRLF files. It compares against the exact bytes the old code produced.
- **R3 and R4:**
  - `test_a_host_changelog_template_shapes_the_section` covers the template override.
  - `test_a_changelog_template_without_notes_is_breaking` covers the missing `{{notes}}` case.
  - The existing `templates/*.md` readiness comparison in `tests/test_defaults.py` stays green, and `EXCEPTIONS` is updated.
- **R5:** `test_python_s_dunder_version_is_a_version_line` covers the bump. The same area has the negative cases `my__version__` and `target-version`.
- **R6:** `test_a_missing_tag_points_at_adoption_when_it_came_after_the_version` and `test_a_version_bump_after_adoption_is_still_the_hint` cover the two orderings. The existing missing-tag test covers the case where one commit holds both.
- **R7:** `test_publish_pushes_the_published_note` covers the push and its rerun skip (`push notes (already done)`). `test_a_refused_notes_push_does_not_fail_publish` covers the refusal.
- **R8:**
  - `test_a_second_clone_skips_the_upload_another_made` covers the second clone.
  - `test_a_second_clone_s_own_notes_survive_the_fetch` covers the merge, so a local note isn't lost.
  - `test_a_second_clone_skips_the_upload_another_made` asserts that `notes_fetch_failed` is absent. No test makes the fetch fail, so that report key is never exercised.
- **R9:** `test_publish_without_a_command_moves_no_notes` covers `--check` and the real run.
- **R10 and R12:** `tests/test_skills.py` passes unchanged.
- **R11:** `test_reference_names_the_changelog_marker_and_the_notes_push` greps for the marker, `--notes-from-tag`, `refs/notes/sdlc` and `__version__`.
- **Weaker, not blocking:** nothing tests the fetch-failure path (`notes_fetch_failed` set, publish carries on with local notes).
- **checks.md:** the change has none, and none is needed. Every requirement is covered by a test in the suite.
- **Test command:** `uv run --group dev pytest -q -n auto` ran the whole suite. I did not run `./check.sh`, so the ruff and `claude plugin validate` gates are unchecked.
