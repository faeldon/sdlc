---
id: 185
slug: landing-gates
kind: plan
created: 2026-11-19
updated: 2026-11-19
---

# 185 — The landing runs every gate a hand-built change gets, and stops only for what wasn't approved · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/landing.py`: `checks_sha()`, `read_only_command()`, `checks_clearance()`
  and `build_due()` (new); `_train_begin()` records `checks_sha` and `checks`; `_train_reading()`
  step 4 names `accept` with its clearance or `checks`, and step 3 is followed by `_train_build()`
  and `_read_builds()` (new); `_run_plan()` runs a cleared `accept` after `_clearance_now()`
  (new) agrees; `_run_loop()`'s failed rule exempts `accept`; `RUN_STEPS` gains `accept`,
  `checks`, `build`; `TRAIN_STEPS` gains `checks`, `build`; `RUN_STOPS` keeps `accept` and its
  comment says why; `land_question()` gets R10's clauses; `cmd_land_check()` adds `build` per
  change; `_not_already_made()` worded once (-47); docstrings (module, `land_verdict`).
- `plugins/factory/scripts/factory.py`: `_base_command()` (new), with `_base_check()` kept as its
  `check` call so its five callers and the hand gate's tests don't move; `cmd_gate(..., build)`
  and `--build`; `land_build_path()`, `land_checks_path()` (new); `CHECKS_RE`; the `land-checks`
  task in `TASKS`, `TASK_ROLE`, `TASK_PURPOSE`, `LAND_TASKS`, `LAND_TASK_STEP` (`recheck`),
  `PROMPT_PARTS`, `TASK_PROMPTS`; `_land_task()`'s `land-checks` branch; `cmd_agent()` files the
  reply under `Judged: <sha16>`; `holds()` takes the task; `taken_lines()` (-48); `purpose_of()`'s
  docstring (-36); `cmd_accept()`'s and `_run_check()`'s docstrings.
- `plugins/factory/prompts/land-checks.md` (new): the approver's question.
- `tests/train_driver.py`: `DRIVER_STEPS` and `drive_train()` take `checks` (a HARMLESS record by
  default, `checks=` to say otherwise) and `build` (`cmd_gate(..., build=True)`).
- `tests/test_train.py`: R1–R9 and R11–R16 tests, R5, R7 and R8 portable unit tests among them;
  `test_the_loop_runs_only_its_named_commands` and `test_the_train_driver_takes_every_step_a_
  reading_names` updated to the new rule (`accept` is now both a step and a stop).
- `tests/test_land.py`: R10's question cases, R17's refusal loop, R18's case in
  `test_the_nits_taken_in_line_is_read_in_its_forms` (it lives here, not in test_factory).
- `tests/test_factory.py`: R19.
- `tests/test_prompts.py`, `tests/prompts/land-checks.txt` (new): the prompt's pinned copy.
- `tests/test_modules.py`: `checks_clearance` and `checks_sha` join `LANDING_NAMES`, since
  `factory.py`'s `_land_task()` and `cmd_agent()` call them (the module rule).
- Docs (R20): `AGENTS.md`'s factory paragraph, `plugins/factory/README.md`,
  `plugins/factory/skills/land/SKILL.md`.

Reused, not re-derived: `_preflight()` (the checks as `sdlc.py accept` parses them),
`opening()`, `_changed_paths()`, `risk_paths()`/`_sensitive()`, `_run_check()`, `gate_slot()`,
`_tree_hashes()`, `_placeholders()`, `read_gate_file()`, `_is_ancestor()`, `_amend_record()`.

## Work order

1. **The nits** (R17, R18, R19): `_not_already_made()`'s wording, `taken_lines()`'s list-item
   stop, `purpose_of()`'s sentence with its behaviour test. Independent of the rest.
2. **The read-only list** (R5): `read_only_command(text, checkout)`, pure, returning why it is
   refused or None. Beyond the spec's list, a short option's glued value (`-f/etc/x`) is checked
   by the path rule too, as a value after `=` is.
3. **The approved checks and the clearance** (R1, R2, R3, R4, R7, R8, R9): `_train_begin()`
   records; `checks_clearance()`; the reading's `accept` with `checks`; `_run_plan()` runs it
   after `_clearance_now()`; the loop's FAIL rule. The driver learns `checks`.
4. **The approver's judgement** (R6): `land-checks` task, prompt, filing, `holds()`; the reading
   names `checks`.
5. **The build** (R11–R16, R10): `_base_command()`, `gate --land --build`, `build_due()`,
   `_train_build()`/`_read_builds()`, `land-check`'s `build`, the question's clauses.
6. **The docs** (R20).

## Tests

- R1 `test_begin_records_each_changes_approved_checks` (test_train)
- R2 `test_unchanged_checks_run_as_stacked_without_a_stop` (loop, two moved changes)
- R3 `test_checks_failing_as_stacked_pause_as_a_review_ejection` (loop)
- R4 `test_a_changed_check_off_the_list_stops_before_the_approver` (loop, fake `claude`)
- R5 `test_read_only_command` and `test_read_only_command_passes` (test_train, parametrized,
  portable)
- R6 `test_changed_read_only_checks_go_to_the_approver` (loop),
  `test_land_checks_refuses_outside_a_changed_train_change`, `tests/prompts/land-checks.txt`
- R7 `test_the_approvers_answer_decides_a_changed_check` (test_train, `_preflight` stood in for)
- R8 `test_harmless_never_clears_a_command_off_the_list` (test_train, through `_run_plan`)
- R9 `test_the_loop_rechecks_before_it_runs_accept` (test_train)
- R10 the `land_question` tests in test_land and test_train, extended
- R11 `test_gate_build_runs_the_bases_build_and_records_it`, `test_gate_build_refuses_without_a_build`
- R12 `test_which_changes_call_for_the_build` (parametrized)
- R13 `test_a_train_of_one_runs_the_build_before_it_lands`
- R14 `test_a_red_build_stops_the_train`
- R15 `test_no_build_runs_unless_a_change_calls_for_it`
- R16 `test_a_build_rounds_gate_never_runs_the_build`
- R17 the refusal loop in test_land; R18 the nits-taken-in test; R19
  `test_a_run_with_no_figures_leaves_the_next_try_its_own_purpose` (test_factory)
- R20 by the acceptance check in `checks.md` (the spec's Verification grep, and the new names
  in each doc), and the review.

## Rollback

`git revert` undoes all of it. Nothing outside the repo is written. A train begun under this
change has `checks_sha`/`checks` in its state file in the git common dir; the reverted code
ignores the keys. A `build/land-<n>.build.md` or `build/land-<n>.checks.md` already committed in a
landed change stays in that change's history, read by nothing after a revert.
