The build of 185 is done and uncommitted: R1–R20 are built and the repo's full gate passes.

## What was built

1. **The three nits (R17–R19).**
   - The empty-fix refusals in `landing.py` now say `FIX: ALREADY MADE` at most once, and the report's path is relative to the change folder so the lines stay short.
   - `taken_lines()` in `factory.py` now stops a `Nits taken in:` line at an indented list item, so a sub-bullet that names an id to say it's left out no longer retires it.
   - `purpose_of()`'s docstring now says a run that reports no cost figures writes no row.
2. **The read-only list (R5).** `read_only_command(text, checkout)` returns why a command is refused, or None when it passes. It goes slightly beyond the spec: a value glued to a short option (`-f/etc/passwd`) gets the same path check as a value after `=`.
3. **Approved checks and when they may run (R1–R4, R7–R9).**
   - `train --begin` records each change's `checks_sha` and `checks`.
   - `checks_clearance()` decides whether a change's checks may run without the person. The reading names `accept` with that answer, or `checks` when the approver still has to judge.
   - The loop runs a cleared `accept` itself. `_run_plan()` re-reads the clearance from `checks.md` just before running it, and a failing `accept` is now read by the next reading, as a failing gate is.
4. **The approver's judgement (R6).** A new `agent --task land-checks` runs the approver with the new `prompts/land-checks.md`. Its reply is filed in `build/land-<n>.checks.md` under `Judged: <sha16>`, and `holds()` now takes the task into account.
5. **The build check (R10–R16).**
   - `gate --land --build` runs the base branch's `[commands] build` and writes `build/land-<n>.build.md`.
   - `build_due()` decides which changes call for it. The train runs it once at the tip after the gate; a red build stops the train and is never bisected.
   - `land-check` now reports `build` for each change, and the landing question gains the new clauses.
6. **The docs (R20).** Updated the factory paragraph in `AGENTS.md`, `plugins/factory/README.md`, the land skill (Step 3, the steps list, the stops, Resuming, Out of scope), and the docstrings the spec lists. `checks.md` holds one acceptance check that these doc edits stay in place.

**Tests added.** Each requirement has the test named in the spec, all in `tests/test_train.py` except R17/R18 (`test_land.py`, which also gets the R10 question cases), R19 (`test_factory.py`) and the prompt's pinned copy (`tests/prompts/land-checks.txt`). The shared test driver (`tests/train_driver.py`) now handles the new `checks` and `build` steps. I updated two existing tests the spec said would change, because `accept` is now both a step the loop runs and a stop.

**Not test-first:**
- The R7, R8 and R9 tests passed the first time they ran, because I wrote that part of the clearance together with R2–R4. To show they catch real breakage, I broke the code three ways and saw them fail, then restored it.
- R19 pins behaviour that was already there; the nit was only the docstring.

**Changes from `plan.md`, now recorded in it:**
- The R5, R7 and R8 unit tests live in `test_train.py`, not `test_land.py`.
- R18's test is in `test_land.py`.
- I kept `_base_check()` as a one-line wrapper around `_base_command(root, base, "check")`, so none of its callers had to change.
- `checks_clearance` and `checks_sha` were added to `LANDING_NAMES` in `tests/test_modules.py`, because `factory.py` calls both.

**Left in `notes.md`:** the land skill's frontmatter description doesn't yet mention the build at the tip or the approver's judgement.

- UNTESTABLE: none

## Decisions

- DECISION: [default] Should the read-only list also check a value glued to a short option (`grep -f/etc/passwd`)? Going ahead with yes unless told otherwise.
  - OPTION: check it — closes a way to read outside the checkout that the spec's rules leave open; a harmless glued value pays the same path check
  - OPTION: the spec's rules only — exactly as written; `-f/abs/path` slips past the list and only the approver would catch it
  - WHY: R4 and R8 rest on the list refusing reads outside the checkout
- DECISION: [default] Should R17's evidence lines keep naming a long command in full, even past 160 characters? Going ahead with yes unless told otherwise.
  - OPTION: keep them whole — the refusal shows the exact command; a very long command makes a long line
  - OPTION: truncate them — every line stays under 160; the person loses part of the command they need to see
  - WHY: those lines come from `read_evidence()`, which the build loop shares; R17's own lines are all short
- DECISION: [default] Should the `AGENTS.md` factory paragraph be edited as the spec's *Contracts touched* section words it? Going ahead with yes unless told otherwise.
  - OPTION: as the spec words it — the map matches the code; it changes the "host command only behind a prompt" contract for anyone reading the map
  - OPTION: hold the edit for separate approval — the contract change gets its own yes; the map is wrong about the code until it lands
  - WHY: the spec says that edit needs explicit approval, and approving the spec may or may not have been meant to cover it

## Evidence

$ uv run --group dev pytest -q tests/test_land.py::test_a_fix_commit_needs_an_ask tests/test_land.py::test_the_nits_taken_in_line_is_read_in_its_forms
2 passed in 3.23s
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py::test_a_run_with_no_figures_leaves_the_next_try_its_own_purpose
1 passed in 2.39s
exit: 0

$ uv run --group dev pytest -q tests/test_train.py -k read_only
44 passed, 59 deselected in 0.17s
exit: 0

$ uv run --group dev pytest -q tests/test_train.py -k "begin_records or unchanged_checks or failing_as_stacked_pause or off_the_list_stops"
4 passed, 103 deselected in 24.28s
exit: 0

$ uv run --group dev pytest -q tests/test_train.py -k "approvers_answer or harmless_never or rechecks_before"
9 passed, 107 deselected in 4.98s
exit: 0

$ (code mutated: answers-agree check, off-list stop, R9 re-read) uv run --group dev pytest -q tests/test_train.py -k "approvers_answer or harmless_never or rechecks_before"
3 failed, 6 passed, 107 deselected in 3.00s
exit: 1

$ uv run --group dev pytest -q tests/test_train.py -k "go_to_the_approver or land_checks_refuses"
2 passed, 116 deselected in 12.17s
exit: 0

$ uv run --group dev pytest -q -n 4 tests/test_train.py -k "gate_build or call_for_the_build or train_of_one_runs or red_build or no_build_runs or build_rounds_gate"
13 passed in 20.34s
exit: 0

$ uv run --group dev pytest -q tests/test_land.py tests/test_train.py -k "question"
3 passed, 215 deselected in 0.08s
exit: 0

$ uv run --group dev pytest -q tests/test_prompts.py
61 passed in 0.88s
exit: 0

$ uv run --group dev pytest -q tests/test_modules.py
28 passed in 3.68s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_train.py tests/test_land.py tests/test_factory.py tests/test_prompts.py tests/test_modules.py
695 passed, 1 skipped in 278.74s (0:04:38)
exit: 0

$ uv run --group dev ruff check . && uv run --group dev ruff format --check .
All checks passed!
315 files already formatted
exit: 0

$ sh -c "<checks.md's block>"
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 185
All checks passed!
3381 passed, 29 skipped in 202.40s (0:03:22)
✔ Validation passed
exit: 0
