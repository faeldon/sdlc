R8 is fixed: your words for a fix no longer reach a command line. The land skill writes them into the change's `decisions.md` as a ticked line, and `land-fix --ask` only takes that line's id. The full gate passes with 2020 tests, and the work is left uncommitted.

## How it works now

- **The command (`factory.py`):** `land-fix <NNN> --ask R<k>` only accepts a ticked `- [x] R<k> (person, fix): <words>` line in `decisions.md`. The new `read_fix_words()` reads that line, the same way `read_revision()` and `read_restart_words()` read theirs. The words are copied into `build/land-<n+1>.ask.md` exactly as written. It refuses an id with no such line, an unticked line, a line of another kind (`revise`, `restart`), or raw words passed in place of an id. A refusal opens no round. The ledger skips the line because it only reads `D<k>` lines.
- **The land skill:** after the yes, Step 3.4 writes your words at the end of the change's `decisions.md` (in the worktree `land-check` named) as `- [x] R<n> (person, fix): …`, with `<n>` one past the highest `R` already there. It then runs `land-fix <NNN> --ask <R1>`. The skill now has `Write` and `Edit` for this, which is how the build skill handles `--revise` and `--words`. It is still the one question, and nothing is written before the yes.
- **`plan.md`:** this approach is added under `cmd_land_fix()`, the skill's Step 3.5 and Tests.
- **`spec.md`:** I reworded R8 and the Design's `--ask` bullet to match what was built, since the reviewers check against the spec. You may want to look at that edit.
- **`plugins/factory/README.md`:** it now says your words go to `decisions.md`, never a command line. I also rewrapped the long lines the reviewer flagged in that paragraph.

## Tests added
- `test_a_fix_is_asked_by_its_line_in_decisions_md_never_on_a_command_line` (`tests/test_land.py`): uses words containing `"`, `'`, `$(rm -rf ~)` and backticks. It checks each refusal above, that no round opens on a refusal, that the words reach the ask file unchanged, and that the ledger stays empty.
- `test_the_land_skill_passes_a_fixs_id_never_its_words` (`tests/test_skills.py`): the skill runs `--ask <R1>`, never `--ask "`, names the `(person, fix)` line, and has `Write` and `Edit`.
- The existing fix tests now pass an id through a small `_asked()` helper that writes the line.

Both new tests and the main fix test failed first for the expected reason (the script wrote `R1` into the ask file, and the skill still quoted the words), then passed.

## Left as they were
- **`notes.md`:** the only item is now ticked, with a line saying what was done. `land-check` will no longer leave 104 out of a batch because of it.
- **The reviewer's `inbox.md` nit:** this is the normal `[building]` tag. `sdlc.py` keeps it on the change's branch until ship (line 6840), so I didn't touch it.
- **The reviewer's other optional items are not done:** the "go to 4" wording, re-asking for the fix after `moved`, and `--commit` checking that `build/land-<n>.md` exists first. The decision didn't ask for them.

No new decisions this round. D1–D3 were confirmed in `decisions.md`, and I built on those answers.

## Evidence

$ uv run --group dev pytest -q -n auto tests/test_land.py -k "fix" tests/test_skills.py -k "fix"   (before the code)
FAILED tests/test_skills.py::test_the_land_skill_passes_a_fixs_id_never_its_words
FAILED tests/test_land.py::test_a_fix_is_asked_by_its_line_in_decisions_md_never_on_a_command_line
FAILED tests/test_land.py::test_a_fix_asked_at_landing_is_built_gated_and_reviewed_at_depth
3 failed, 2 passed in 2.44s
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_land.py tests/test_skills.py -k "fix"
5 passed in 27.49s
exit: 0

$ ./check.sh
All checks passed!
2020 passed in 40.62s
✔ Validation passed
✔ Validation passed
exit: 0
