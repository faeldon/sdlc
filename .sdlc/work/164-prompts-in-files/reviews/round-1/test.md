VERDICT: PASS

Every requirement has a test that fails without it, and the recorded copies match the old script's output.

## Notes

**Requirement coverage**
- R1: `test_no_prompt_prose_in_the_script` checks a fixed phrase list against `factory.py`'s source. `grep -c 'Address every KEPT line\|keeping what both sides meant'` also gives 0.
- R2: `test_every_prompt_matches_its_recorded_copy` is parametrised over 45 cases. That is every row of the spec's table (`tests/prompts/*.txt` holds 45 copies).
- R3: I ran the cross-check against a `git archive` of the merge-base's `plugins/factory/scripts/`, with `SDLC_FACTORY_UNDER_TEST` set. `-k matches_its_recorded_copy` gave `45 passed, 14 deselected`, so the copies are the old script's output.
- R4: `test_every_prompt_part_is_rendered` spies on `prompt_part` across every case. It also checks the files on disk against `PROMPT_PARTS`.
- R5: five doctored shapes (missing part, extra part, unfilled placeholder, unnamed placeholder, stray `$`) plus a missing file. The parametrised test asserts exit 1, a refusal naming the file and the cause, and no fake-`claude` call.
- R6: `test_filled_text_is_never_read_as_a_placeholder` feeds `$5`, `${round}`, `$$`, `{x}` and backticks through the revise, rework and land-fix paths.
- R7: `test_a_crlf_prompt_file_gives_the_same_prompt` is marked `portable` and rewrites every file as CRLF.
- R8: `test_prompts_are_read_from_the_plugin_alone`.
- R9: `test_prompt_files_hold_no_path`.
- R10: the only edit to `tests/test_factory.py` is `factory.RECHECK` becoming `factory.prompt_part("spec", "recheck")`. That is the rename the spec allows.
- R11: `test_the_factory_readme_names_the_prompts_folder`.

**The run**
- The gate record `build/round-1.gate.md` shows `3019 passed, 28 skipped`.
- I ran `uv run --group dev pytest tests/test_prompts.py -q -n auto`, which gave `59 passed`.

**Checks**
- There is no `checks.md` for this change.

- NIT: tests/test_prompts.py:439: the R5 test only builds the `build` task, so the refusal for a broken `mend.md` or `land-review.md` under `land-mend` is untested. `_task()` validates both files by the same code path, so the risk is low. {tests S low}
