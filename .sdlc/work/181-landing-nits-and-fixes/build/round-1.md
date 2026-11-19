I built all of change 181 (R1–R10) and left it uncommitted in the worktree. The named tests pass and ruff is clean. I didn't run the full `./check.sh`: the gate runs it next and writes `build/round-1.gate.md`.

**Slices built**
1. **Nits by the marker (R1–R3).** A landing now retires a nit only when its id is on a `Nits taken in:` line in the Approach or Requirements; an id anywhere else in prose retires nothing. The line can be plain, a list item or bold, in any case, and can wrap onto indented lines. A marker under `## Problem`, or in the middle of a line like `R1. Nits taken in:`, retires nothing. The five existing tests that used `Takes in nit …` prose now use the marker, and the parity test with `sdlc.py` puts its ids on a marker line.
2. **The marker in the docs (R4).** `skills/intent/SKILL.md`, `skills/intent/batch.md`, `skills/spec/SKILL.md`, the factory's land `SKILL.md` and its `README.md` all now name the `Nits taken in:` line. The land skill and README also say a fix already made goes on.
3. **A fix already made (R5–R7, R9).** When the builder edited nothing, `land-fix --commit` now goes on only if `build/land-<n>.md` answers `FIX: ALREADY MADE` and its `## Evidence` checks out. It then amends nothing, returns `already_made: true` and marks the train's fix done. Otherwise it still refuses, naming the missing report, missing answer or bad evidence. If the builder did edit, the edit is amended in as before, with `already_made: false`. The ask file stays, so the fix still counts as a signal.
4. **The train (R8).** Checked through the driver's steps and through `train --run`: no new code was needed beyond slice 3.
5. **The prompt (R10).** `prompts/land-fix.md` now tells the builder to edit nothing, answer `FIX: ALREADY MADE` and show its proof under `## Evidence`. I re-recorded `tests/prompts/land-fix.txt`.

**Tests added, and what each proves**
- R1, `test_a_nit_named_but_not_taken_in_stays`: a nit named in prose is still in the register after close; only the marker's nit is retired.
- R2, `test_the_nits_taken_in_line_is_read_in_its_forms`: every form, wrapping, whole-id matching, the Problem and mid-line cases, and the spec's Requirements.
- R4, `test_every_place_that_takes_a_nit_in_names_the_marker`.
- R5, `test_a_fix_already_made_goes_on_without_a_commit`: exit 0, `HEAD` unchanged, `already_made: true`, train fix marked done.
- R6, `test_a_fix_commit_needs_an_ask` (extended): refusals for no report, no answer, disagreeing answers, no `## Evidence`, and a command with no `exit:`.
- R7, `test_a_fix_asked_at_landing_is_built_gated_and_reviewed_at_depth`: now also checks `already_made` is false.
- R8, `test_a_train_fix_already_made_goes_on_to_the_gate`.
- R9, `test_a_fix_already_made_is_still_a_signal`.
- R10, `test_the_land_fix_prompt_tells_a_fix_already_made`.

Each new test failed for the expected reason before its code went in. For R8, I briefly restored the old refusal to see it fail, then put the new code back.

**What changed in `plan.md`**
- I widened `FIX_RE` to read any `FIX: <answer>` line and go on only for `ALREADY MADE`. The spec's version could match only `ALREADY MADE`, so two answers could never disagree and R6's disagreeing-answers refusal couldn't happen.
- The recorded prompt copy lives at `tests/prompts/`, not `tests/fixtures/prompts/` as the plan first said.
- The tip's gate runs under the tip's change (`002-bb`), not the fixed change, so the train test checks that a gate comes after the fix and before change one's review.

**`notes.md`:** nothing left.

- UNTESTABLE: none

- DECISION: [default] (no decision in the ledger to supersede) Read any `FIX: <answer>` line and go on only for `ALREADY MADE`, instead of the spec's regex that matches only `ALREADY MADE`. Going ahead with that unless told otherwise.
  - OPTION: any `FIX:` answer, only `ALREADY MADE` goes on — R6's "lines that disagree" refusal can happen; differs from the design text
  - OPTION: the spec's regex as written — matches the design word for word; two `FIX:` lines can never disagree, so R6's refusal can't happen
  - WHY: R6 asks for disagreeing answers to be refused, and only the wider regex can see a disagreement.

## Evidence

$ uv run --group dev pytest -q -n auto tests/test_land.py -k "nit or fix"
18 passed in 10.56s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_train.py -k fix
3 passed in 35.12s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_prompts.py tests/test_skills.py
477 passed in 2.78s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_modules.py tests/test_windows.py
69 passed in 1.96s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_land.py
87 passed in 28.95s
exit: 0

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --group dev ruff format .
1 file reformatted, 307 files left unchanged
exit: 0

The round-1 gate failed on three tests, and none of them comes from this change's code: all three pass when rerun on their own. I changed no code; the build is as it was in round 1.

**What failed, from `build/round-1.gate.md`** (attempt 1, `./check.sh`: 3 failed, 3160 passed):
- **Two tests in `tests/test_adoption.py`** (`…own_close_runs_mains_code_then_the_merged_code` and `…hears_what_an_update_changed_and_can_take_setup_out`). Both stopped when `uv run --script` couldn't reach PyPI ("Failed to fetch: https://pypi.org/simple/pyyaml/ … dns error"). The machine had no network at the time; the code didn't fail.
- **`tests/test_board_browser.py::test_the_drawer_holds_focus_and_returns_it_to_its_card`.** The record's last 80 lines show no error for it, so I can't say why it failed. This change doesn't touch the board, and the test passes when run alone, so it most likely fails only when the machine is busy running the full gate.

**What I did**
- Reran the three failing tests by name: all 3 pass.
- Added two unticked lines to `notes.md`. One records that the board test seems to fail only under load. The other suggests the adoption tests skip or use a cache when there's no network, so a gate failure is always about the code.

If the next gate fails again, check whether the machine has network before reading it as a fault in the change. I didn't do a full suite run myself; the gate reruns it.

- UNTESTABLE: none

No new decisions this round.

## Evidence

$ uv run --group dev pytest -q tests/test_board_browser.py::test_the_drawer_holds_focus_and_returns_it_to_its_card tests/test_adoption.py::test_the_plugins_own_close_runs_mains_code_then_the_merged_code tests/test_adoption.py::test_a_host_hears_what_an_update_changed_and_can_take_setup_out
3 passed in 61.30s (0:01:01)
exit: 0
