---
id: 155
slug: agent-test-runs-share-the-slot
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 155 — Agents' test runs share the machine with the gate · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`: `_run_check(root, command, capture)`, the one runner of
  the base branch's `[commands] check`, which `cmd_gate()` now calls (its capture, timeout and
  record unchanged); `cmd_check(root, ident)` beside `cmd_gate()`, reusing `find_change()`,
  `_base()`, `_base_check()`, `load_config()["gate_jobs"]` and `gate_slot()`; `FACTORY_SCRIPT`
  and `check_line(folder)`; `_task()` appends `check_line()` to the builder's prompts, and
  `_land_task()` to the resolver's (and the builder's landing prompts); `main()` gains the `check`
  subparser (its variable `p_run`, since `p_check` is `land-check`'s); the docstring names
  `check`.
- `scripts/metrics.py`: `FACTORY_CHECK_RE`, matched beside `HAND_GATE_RE` in `_shell()` and in
  the main session's check events; the docstring's `test_runs=` line names it.
- `plugins/factory/agents/builder.md`: slices run their own tests by name; the gate runs the whole
  suite next; a full run is the prompt's `check` command, in the foreground with the longest
  timeout; the report gives named tests and leaves the gate's result to `round-N.gate.md`; the
  Evidence example a named test run.
- `plugins/factory/agents/reviewer-code.md`, `reviewer-test.md`, `reviewer-behaviour.md`: the gate
  record is the whole suite's result; never run the whole suite another way; named tests only.
- `plugins/factory/agents/resolver.md`: the conflict's tests by name, `check` for a full run, no
  `./check.sh` in the Evidence example.
- `plugins/factory/README.md`: `check` in the slot paragraph and the Mechanism list.
- `AGENTS.md`: *The factory*'s "the one place it runs a host's command" sentence, as the spec's
  Contracts touched words it.
- Tests: `tests/test_factory.py` (R1–R6, R10), `tests/test_metrics.py` (R11),
  `tests/test_skills.py` (R7–R9), `tests/test_train.py` (the resolver's prompt, R6).
- `.sdlc/work/155-…/checks.md` (new): R12's README line.

## Work order

1. **`check` runs the base branch's command** (R1, R2): `_run_check()`, `cmd_check()` with its
   refusals, `main()`'s subparser; `cmd_gate()` moved onto `_run_check()` with its tests unedited.
2. **`check` holds a slot and frees it** (R3, R4): inside `gate_slot()`; timeout and `OSError`
   handled; subprocess tests with `gate_jobs = 1`, the `HOLD` child, a killed `check`.
3. **`check` writes nothing** (R5).
4. **The prompts name it** (R6): `FACTORY_SCRIPT`, `check_line()`, `_task()` and `_land_task()`.
5. **Metrics count it** (R11).
6. **Evidence citing the gate record** (R10): a test only; `is_read()` already reads `cat`/`head`.
7. **Agent prompts** (R7–R9) and their tests.
8. **Docs** (R12): README, AGENTS.md, docstring, `checks.md`.

## Tests

- R1: `test_check_runs_the_base_branchs_command_and_exits_with_its_code`.
- R2: `test_check_refuses_and_runs_nothing` (parametrized: no base, no check, unknown id).
- R3: `test_two_checks_with_one_slot_run_one_after_the_other`;
  `test_a_check_waits_for_a_gates_slot` (the `HOLD` child).
- R4: `test_a_killed_check_frees_its_slot`; `test_a_check_past_the_timeout_is_killed`.
- R5: `test_a_green_check_writes_nothing_and_never_clears_the_gate`.
- R6: `test_the_builders_prompts_name_the_check_command` (build, fix, rework, decided, mend, and
  no reviewer, verifier or approver prompt); the train test asserts the resolver's prompt.
- R7–R9: `tests/test_skills.py`, one test each for the builder, the reviewers, the resolver.
- R10: `test_evidence_citing_the_gate_record_is_a_read` in `tests/test_factory.py`, beside the
  other `read_evidence()` tests (`tests/test_evidence.py` is the retro's evidence script, not
  this parser).
- R11: rows added to `test_a_test_run_is_known_by_its_program`.
- R12: `checks.md`'s README grep.

## Rollback

`git revert` undoes all of it: `check` writes nothing, takes the same slot lock files `gate`
already makes, and nothing is published.
