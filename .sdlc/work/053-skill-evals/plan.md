---
id: 053
slug: skill-evals
kind: plan
created: 2026-11-12
updated: 2026-11-13
---

# 053 — Behavioural evals for the core skills · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `evals/` (new): `scaffold.sh`, `fixtures/` (`base`, `built`, `built-open-finding`, `tier2-plan`,
  `shipped`), and six cases (`intent`, `spec`, `ship`, `ship-open-finding`, `close`, `idea`), each
  `prompt.md`, `case.yaml`, `scaffold.sh` and `graders/`.
- `scripts/sdlc.py`: `cases`, `cases compare` and `run-cases` (`case_tags()`, `cases_scope()`,
  `compare_runs()`, `cases_argv()`, `_cases_report()`, `cases_nudge()`); `preflight`'s `cases`
  part; `findings.md`'s `Skill evals:` note (`CASES_RE`, `_note_says()`); `ship_question()`'s
  clause and `cmd_ship`'s refusal; release's `cases`; status's nudge.
- `skills/ship/SKILL.md`, `skills/release/SKILL.md`.
- `tests/test_evals.py` (new); `tests/test_findings.py`, `tests/test_skills.py`,
  `tests/test_adoption.py` (R16); `tests/conftest.py` (the fake `gh`, moved from
  `tests/test_archive.py`).
- `AGENTS.md`, `docs/CONTRIBUTING.md`.

## Work order

1. Probe that a slash command expands in a `plugin eval` run (passed: 3 turns, $0.14), then the
   spec corrections it and planning found (no `eval` in a command name; `cases` out of
   `READ_ONLY`).
2. Fixtures and the shared scaffold, with the test that builds each and runs `check --strict`.
3. The six stop-at-WAIT cases, with the tests that pin their graders.
4. The script's commands, and their tests.
5. Debug runs: `--tag` for `--case`, uv readied in the run's home, graders that read the script
   held in a variable, a test in the `built` fixture.
6. Ship's hook, release's advice, status's nudge; R13's guards; R16.
7. The approve path (R3, R5, R6) carried forward (`notes.md`); docs; the gate.

## Tests

- R1, R2, R4, R15: `test_every_fixture_passes_check`, `test_a_stop_case_keeps_every_never_write_grader`,
  `test_the_never_graders_match_what_they_forbid`, `test_the_cases_are_read_with_their_tags`,
  `tests/test_nothing_local.py`.
- R7–R9, R14: `test_a_diff_calls_for_the_cases_of_the_skills_it_touches`,
  `test_runs_compare_case_by_case`, `test_a_run_grants_its_tools_and_caps_its_cost`,
  `test_the_report_folder_matches_the_factorys`, `test_a_host_has_no_cases`.
- R10: `test_the_note_says_whether_the_skill_evals_ran`,
  `test_ship_refuses_a_diff_with_cases_whose_note_says_nothing_of_them`,
  `test_the_question_names_skill_evals_that_didnt_run`.
- R12: `test_status_nudges_only_when_claude_code_moved_since_the_last_full_run`.
- R13: `test_no_skill_lets_accept_run_unasked`, `test_the_gate_and_ci_never_run_the_skills_cases`.
- R16: `test_a_change_closing_an_issue_lands_with_its_closes_line`.
- Manual: the paid runs under `.sdlc/reports/cases-2026-11-13-*`; ship's own scoped run.

## Rollback

`git revert <sha>`. It leaves nothing outside the repo: run results sit in the ignored
`.sdlc/reports/`, and no host runs the suite.
