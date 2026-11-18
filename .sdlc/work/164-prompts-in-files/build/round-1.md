Every factory prompt is now read from text files under `plugins/factory/prompts/`, and the text agents receive is byte-for-byte what the old script sent. The full gate is green (3019 passed, 28 skipped), and everything is left uncommitted.

**How I proved the text is unchanged (R2, R3).** Before touching `factory.py`, I added `tests/test_prompts.py` and recorded 45 prompts from the unchanged script into `tests/prompts/`. That covers every branch in the spec's table. Each case uses a made-up loop state, with git and the landing train replaced by fixed fakes so commit ids don't vary. Only the temp root and the script's path are swapped for a fixed mark before comparing. I then ran the same test against a copy of the base branch's `scripts/` (`SDLC_FACTORY_UNDER_TEST`): all 47 golden-copy tests (the 45 cases and the check that each recording has a case) pass, and the 12 tests of the files themselves are skipped.

**Slices built:**
1. **Prompt files.** `common.md` plus one file per task: `spec`, `build`, `fix`, `review`, `verify`, `rework`, `approve`, `decided`, `mend`, `resolve`, `train-resolve`, `land-fix`, `land-review`, `land-verify`. Each has a title, a note, then `## <part>` sections, one line each, with `${name}` placeholders.
2. **The reader in `factory.py`.**
   - `PROMPTS_DIR` points at the plugin's own `prompts/` folder.
   - `PROMPT_PARTS` lists, for each file, its parts and the placeholders the script fills in each.
   - `_prompt_file()` reads a file and refuses it if a part is missing or extra, a placeholder doesn't match, or a `$` is stray.
   - `prompt_refusal()` runs first in `_task()`, so a bad file stops the step before any session starts.
   - `prompt_part()` fills a part with `string.Template`.
3. **The prompt code.** `_task_prompt`, `_land_task`, `check_line`, `weigh_text` and `_land_diff` now pick parts and join them. The decision logic and joiners are unchanged. `MEND`, `VERDICT_MEND`, `DECISION_MEND`, `VERIFY_MEND` and `RECHECK` are gone. `RECONSIDER` and every refusal message stay in code. `landing.py` is not touched.
4. **README.** `plugins/factory/README.md` now says where the prompts live, that they're read only from the plugin, and how placeholders are written.

**Tests added and what they prove:**
- R1 `test_no_prompt_prose_in_the_script`
- R2/R3 `test_every_prompt_matches_its_recorded_copy` (45 cases), plus `test_every_recorded_copy_is_a_case`
- R4 `test_every_prompt_part_is_rendered`
- R5 `test_a_prompt_file_that_doesnt_match_is_refused` (5 shapes, through `cmd_agent` with a fake `claude` that is never called), plus `test_a_missing_prompt_file_is_a_refusal`
- R6 `test_filled_text_is_never_read_as_a_placeholder`
- R7 `test_a_crlf_prompt_file_gives_the_same_prompt` (marked `portable`)
- R8 `test_prompts_are_read_from_the_plugin_alone`
- R9 `test_prompt_files_hold_no_path`
- R11 `test_the_factory_readme_names_the_prompts_folder`

**R10:** the only edit to existing tests is one line in `tests/test_factory.py`: `factory.RECHECK` becomes `factory.prompt_part("spec", "recheck")`. All tests in `test_factory.py`, `test_land.py` and `test_train.py` pass otherwise unedited.

**Named runs:**
- New tests: red first, for the expected reasons (missing `PROMPTS_DIR`/`prompt_part`, prose still in the script, README).
- After the code: 59/59 in `test_prompts.py`.
- 610 passed across `test_prompts`, `test_factory`, `test_land`, `test_train`, `test_nothing_local`, `test_windows` and `test_modules`.
- 1 portable test passed.
- The cross-check against the base branch's script: 47 passed, 12 skipped.

**Changes to `plan.md`:**
- I rewrote it from the scaffold.
- `prompt_part(name, key, /, **values)` takes the file and part positionally, because `train-resolve` has a `${name}` placeholder that clashed with the parameter.
- A task's own files are checked before `common.md`.
- Commit ids are fixed by the fake git in the tests, so they need no mark.

**Left in code on purpose, as fill-in values rather than prompt text:**
- the `'none'`/`'nothing'` fill-ins for an empty list;
- `"the base branch"` as `base`'s fallback;
- `cmd_agent`'s screenshot suffix, which the spec says to ask about before moving.

Nothing went into `notes.md`. I raised no decisions.

## Evidence

$ SDLC_RECORD_PROMPTS=1 uv run --group dev pytest tests/test_prompts.py -q -x   (against the unchanged factory.py)
46 passed in 0.10s
exit: 0

$ uv run --group dev pytest tests/test_prompts.py -q   (new tests, before the code)
11 failed, 48 passed in 8.23s
exit: 1

$ uv run --group dev pytest tests/test_prompts.py tests/test_factory.py tests/test_land.py tests/test_train.py tests/test_nothing_local.py tests/test_windows.py tests/test_modules.py -q -n auto
610 passed in 78.55s (0:01:18)
exit: 0

$ SDLC_FACTORY_UNDER_TEST="$D/old164/scripts/factory.py" uv run --group dev pytest tests/test_prompts.py -q   (base branch's scripts via git archive of the merge base)
47 passed, 12 skipped in 0.14s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 164
All checks passed!
3019 passed, 28 skipped in 120.40s (0:02:00)
✔ Validation passed
✔ Validation passed
exit: 0

$ grep -c 'Address every KEPT line\|keeping what both sides meant' plugins/factory/scripts/factory.py
0

$ uv run --group dev pytest -q tests/test_prompts.py
59 passed in 9.51s
exit: 0

$ uv run --group dev pytest -q -m portable tests/test_prompts.py
1 passed, 58 deselected in 8.03s
exit: 0
