VERDICT: PASS

Both fixes have a test that fails without them. I ran the two new tests by name and both pass. The gate record `build/land-1.gate.md` shows `3725 passed, 29 skipped in 200.26s` and a passing plugin validation.

## Notes
- **Short and common names.** `test_upstream_cut_places_short_and_common_names_the_host_holds` covers three behaviours.
  - A two-letter repo, owner or user name is cut as a whole word.
  - A common word that is the host's own owner or repo is cut.
  - Neither `quiz` nor `main` is touched, and neither marks the field unsafe.

  The builder's report says this test failed on `qz by jb, from <path>` before the fix. In `_cut_host`, the two-letter case in the safe check uses a word-bounded match.
- **Relative path with `..`.** `test_upstream_cut_never_keeps_a_relative_path_that_climbs` asserts that `scripts/../../secret/notes.txt` becomes `<path>` while `scripts/sdlc.py` is kept. The test creates both files, so the climbing path really does exist and would be kept without the `..` check. The builder's report says it failed before the fix.
- **No checks.** The change has a `checks.md`, and I did not run it. The landing fix adds nothing to it, so I judged no section of it.
- **Commands run.** I ran `uv run --group dev pytest -q tests/test_upstream.py -k "short_and_common or climbs"`, which gave `2 passed`.
- NIT: tests/test_upstream.py:443: the one-character-name case, which is never cut, has no assertion, so loosening that rule would go unnoticed {tests S low}
