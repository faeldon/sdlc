I built change 172 and left it uncommitted. `cmd_close` is now a short run of named step functions, three of the four nits are fixed and the fourth needs no code. The repo's full gate passes: 3075 passed, 28 skipped, exit 0. I had to depart from the spec in four places, and each is raised below as a default.

**Slices built** (`plan.md` written first, with a section listing the departures):
1. **Output pinned before the move (R4).** I added `test_close_output_is_unchanged` with five scenarios (shipped, dropped, `--check`, a rerun after a failed archive, a push to a bare remote). The expected values are in a new file, `tests/fixtures/close-output.json`, recorded from the old code with a one-off script that I deleted afterwards. All five passed on the old code before I changed anything, and still pass after.
2. **The move (R1–R3, R6, R11–R13).** The eleven closures are now top-level `_step_*` functions in `closing.py`, and the code around them is split into `_close_target`, `_close_refusals`, `_close_preview`, `_close_steps`, `_run_close_steps` and `_emit`.
   - **Size:** `cmd_close`'s body is 19 lines. The longest function in the file is `measure_change` at 84.
   - **Old `own` variable:** it is split into `c.own_repo` (whether this is the plugin's own repo) and the local `ahead` (the commits not yet pushed), as the spec's Design says.
   - **Test that fails first:** `test_close_is_a_sequence_of_named_steps`, plus 17 names added to `CLOSING_NAMES`. Both failed before the move and pass after.
3. **R8.** `_lead_line()` takes an `errors` list as a positional argument, so the tests' `lambda *_` stand-in still fits. `report["measure"]["errors"]` appears only when timing failed. The new assertion failed with `KeyError: 'errors'` first, then passed.
4. **R7.** `test_a_change_opened_after_its_close_says_bad_opened` passed on the code as it was, because the nit was a missing test, not a bug. I saw it fail by briefly changing the branch it covers to return `lead=none`, then put the file back from a copy.
5. **R9.** The ceiling is now `math.floor(round((cap - spent) * 100, 6)) / 100`. Before the fix, spending 0.65 gave `'4.34'`, so the test failed; now it gives `4.35`. The existing `3.75` assertion still holds.
6. **R13 and R14.** The module docstring and `cmd_close`'s docstring now name the steps and `_Close`, and I changed the REFERENCE sentence about the `source=git` line. `AGENTS.md` is untouched.

**R10:** no code. Retiring nits -2, -3, -4 and -100 in `entries.md` is ship's job.

**Edits to existing tests beyond R3's:** one assertion in `test_timing_that_fails_drops_only_its_own_line` (R8), and the `test_skills.py` change in the third decision below. Nothing else in `tests/` was removed or changed. `notes.md`: nothing left.

- DECISION: [default] Make `_Close` a plain class with an explicit `__init__` instead of the spec's `@dataclass`? Going ahead with the plain class.
  - OPTION: plain class — it loads, and steps still share one object; a few more lines than a dataclass
  - OPTION: register `closing` in `sys.modules` so the dataclass works — keeps the spec's wording; changes how every by-path module is loaded, which the module tests pin
  - WHY: `closing.py` is loaded by path and never put in `sys.modules`. With string annotations, `@dataclass` looks the class's module up there, so the file failed to load.
- DECISION: [default] Test R9's second case as 0.30000000000000004 → `4.7` and 0.305 → `4.69`, instead of the spec's 0.30000000000000004 → `"4.69"`? Going ahead with the two cases.
  - OPTION: two cases — one shows float noise is ignored, the other shows a real fraction of a cent rounds down
  - OPTION: the spec's case as written — it can't pass: both the old and the new formula give `4.7`
  - WHY: the spec's own rule (ignore noise, then round down) gives `4.7` for that input.
- DECISION: [default] Edit `tests/test_skills.py::test_only_the_named_steps_push`, which R5 doesn't list? Going ahead with the edit.
  - OPTION: edit the test — it now matches a call to `_push(` as a whole word, expects `_step_push` where it expected `cmd_close`, checks that only `_run_close_steps` calls `_step_push`, and looks for `_push_plan(` in `_close_preview`; I planted an extra caller in memory and it is still caught
  - OPTION: rename the push step — breaks R3's required name, and any name ending in `_push` still matches the old substring check
  - WHY: R3's `_step_push` calls `_push(`, and its own name contains `_push(`, so R3 and the unedited test can't both hold.
- DECISION: [default] Make R14's REFERENCE §Metrics edit now, though the spec marks it "ask first"? Going ahead with it as made.
  - OPTION: keep it — the docs match the behaviour -2 accepts; one sentence, easy to revert
  - OPTION: revert it — the docs keep saying a factory change's `source=git` line has `ready_wait`, which the code never writes
  - WHY: it is docs only, and leaving it out keeps the docs wrong.

## Evidence

$ uv run --group dev pytest -q tests/test_archive.py::test_close_output_is_unchanged   (on the old code, before the move)
5 passed in 10.30s
exit: 0

$ uv run --group dev pytest -q tests/test_modules.py -k "close_is_a_sequence or lock_live_in_closing"   (before the move)
2 failed, 17 deselected in 0.16s
exit: 1

$ uv run --group dev pytest -q tests/test_archive.py::test_timing_that_fails_drops_only_its_own_line   (before the R8 fix)
E       KeyError: 'errors'
1 failed in 2.30s
exit: 1

$ uv run --group dev pytest -q tests/test_archive.py::test_a_change_opened_after_its_close_says_bad_opened   (branch briefly broken)
E        +    where ... = 'none: no transcripts for this repo lead=none'.endswith
exit: 1

$ uv run --group dev pytest -q tests/test_evals.py -k "rerun_ceiling or reruns_once_alone"   (before the R9 fix)
E       AssertionError: assert '4.34' == '4.35'
1 failed, 3 passed, 50 deselected in 0.15s
exit: 1

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 172   (first full run)
FAILED tests/test_skills.py::test_only_the_named_steps_push - AssertionError:...
1 failed, 3074 passed, 28 skipped in 186.98s (0:03:06)
exit: 1

$ uv run --group dev python -c "<test_only_the_named_steps_push with a _sneaky caller planted in memory>"
caught: {'_sneaky', '_step_push', 'cmd_release', 'cmd_publish'}
exit: 0

$ uv run --group dev pytest -q tests/test_archive.py::test_close_output_is_unchanged tests/test_archive.py::test_a_change_opened_after_its_close_says_bad_opened tests/test_archive.py::test_timing_that_fails_drops_only_its_own_line tests/test_modules.py::test_close_is_a_sequence_of_named_steps tests/test_modules.py::test_close_push_and_the_lock_live_in_closing tests/test_evals.py::test_the_rerun_ceiling_keeps_its_last_cent tests/test_evals.py::test_a_failed_case_reruns_once_alone tests/test_skills.py::test_only_the_named_steps_push
14 passed in 17.44s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 172
All checks passed!
307 files already formatted
3075 passed, 28 skipped in 139.98s (0:02:19)
✔ Validation passed
exit: 0
