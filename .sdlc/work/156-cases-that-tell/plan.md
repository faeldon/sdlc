---
id: 156
slug: cases-that-tell
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 156 — The skills' cases tell what a skill did, and stop a landing only when you say so · plan

> Written by the builder after reading `cmd_run_cases()`, `cases_argv()`, `compare_runs()`,
> `_run_summary()`, `_cases_report()` and release's report in `scripts/sdlc.py`; `cmd_cases()`,
> `_note_line()`, `land_parts()`, `land_shown()`, `land_signals()`, `land_question()` and
> `_land_readiness()` in `plugins/factory/scripts/factory.py`; the land, ship (`cases.md`) and
> release skills; `tests/test_evals.py` and `tests/test_land.py`; and real kept runs.

## Files to change

What the spec left to check first, read from the machine's kept runs:

- **No grader reads the workspace's final state, and `tool_used` takes one `tool`** (`claude plugin
  eval --help` lists none; every result's `graders[].config` holds one `tool`). R2 uses the `llm`
  grader with `focus: trace`, as the spec says.
- **`--keep-temp`'s layout**: `tracePath` is `/private/tmp/e-<id>/out/trace.jsonl`; `e-<id>` is
  mode `dr-x------` and holds `sealed/` at `d---------`, so removing it needs its modes set first
  (`_remove_workspace()` chmods on a refused delete). `/tmp` resolves to `/private/tmp`.
- **A trace's tool results** are lines `{"type": "user", "message": {"content": [{"type":
  "tool_result", "content": "<text>" | [{"type": "text", "text": …}]}]}}`; the marker sits in the
  `content` of the first git call's result (`Exit code 72\n…xcode-select: Failed to locate 'git'…`).
  The fixture is cut from such a trace, its paths made neutral.

Files:

- `evals/ship-behaviour/graders/reads-behaviour.md`: removed (R2).
- `evals/ship-behaviour/graders/says-the-behaviour-check.md`: an `llm` grader, `focus: trace` (R2).
- `scripts/sdlc.py`: `CASE_ENV_MARKERS`, `CAP_WHY`, `case_runs()`, `_environment_run()`,
  `classify_runs()` (`_classify` was taken), `_workspace_of()`, `_remove_workspace()` (every folder
  made writable, never through a link, then one `rmtree`: the handler form can't retry the
  `os.open` a sealed folder refuses), `_keep_traces()`, `case_verdicts()`, `verdict_lists()`,
  `cases_note()`, `cases_failures()` (the reading `factory.py` copies), `_full_history()`,
  `cases_argv()` (gains `case` and `cap`, always `--keep-temp`, loses `keep`), `_eval()`,
  `_cost()`, `cmd_run_cases()` (the rerun, the record), `_run_summary()` (verdicts first),
  `_cases_report()` and release's `cases` report (`full_history`), `run-cases --keep`'s help.
- `plugins/factory/scripts/factory.py`: `cases_failures()` (the pinned copy), `read_cases_note()`,
  `_case_failures()` (the run's `scope.json` in the main checkout, `_all_checkouts()[0]`),
  `_cases_part()` (`land_parts()`' `cases`: `noted`, `failed`, `environment`, `skipped`, `run`),
  `_cases_shown()` (under `land_shown()`'s cases line), `_cases_signals()` (in `land_signals()`),
  `land_question()`'s clause, `cmd_cases()` (writes run-cases' `note` on a failure; `--skip`).
  `_land_readiness()` is unchanged: its `before` already reads `ran` or `skipped` alike (R14).
- `.sdlc/work/156-cases-that-tell/checks.md` (new): R19's docs, an acceptance check.
- `skills/ship/cases.md`: failures with graders and trace; environment and passed-on-rerun no
  finding; the note copied from `note` (R17).
- `plugins/factory/skills/land/SKILL.md`: the cases run in Step 1, before the WAIT; a decline is
  `--skip` (R16).
- `skills/release/SKILL.md`: the last full run's verdicts beside the one before (R18).
- `docs/CONTRIBUTING.md`, `AGENTS.md` (*Writes before a WAIT*), `plugins/factory/README.md` (R19).
- `tests/fixtures/eval-trace-no-git.jsonl` (new): cut down from a kept trace (R8).
- `tests/test_evals.py`: R1, R2, R4–R10, R18 tests; the argv test updated for `--keep-temp`.
- `tests/test_land.py`: R11–R15 tests; the old "a failed case writes nothing" turned around; the
  `cases` part's new keys.
- `tests/test_factory.py`: the pinned copy of `cases_failures()`.
- `tests/test_skills.py`: `test_no_skill_grants_the_cases`; the land skill's Step 1 runs the cases.

Reused: `compare_runs()` for scores and `fell`; `_read_json()`; `_case_runs()`; `_note_line()`,
`_note_says()`, `_record_land()` and `CASES_RE` in `factory.py`; `_sdlc()`.

## Work order

1. **Graders (R1–R3).** `test_no_grader_insists_on_a_tool` red on the two, then the grader edits and
   the rewritten behaviour-case test.
2. **Environment (R8).** The fixture, `_environment_run()`, its test.
3. **Verdicts and the note (R5, R7, R10).** `case_runs()` reads a result's runs (score, failing
   graders, trace); `case_verdicts()` decides each case for either scope; `cases_note()` words the
   line. Pure, tested on hand-made results.
4. **Traces and workspaces (R9).** `_keep_traces()` copies a failed run's trace and removes each
   workspace behind the guard; portable test.
5. **The rerun (R4, R6) and the record (R10).** `cases_argv()`' `case` and `cap`; `cmd_run_cases()`
   reruns each failed case once, under what's left of the cap, and writes the verdicts, `failed`,
   `environment`, `passed_on_rerun`, `note` and `left` into `scope.json` and its output;
   `_run_summary()` reads them.
6. **Full history (R18)** in `_cases_report()` and release's report; release skill text.
7. **The factory's note (R11, R12).** `cmd_cases()` writes `note` on a failure, `--skip <why>`.
8. **Landing (R13–R15).** The pinned `cases_failures()`; `land_parts()`, `land_signals()`,
   `land_shown()`, `land_question()`; `_land_readiness()` checked unchanged (R14).
9. **The land skill (R16)** and `test_no_skill_grants_the_cases`.
10. **Ship's `cases.md` (R17).**
11. **Docs (R19).**

## Tests

- R1: `test_no_grader_insists_on_a_tool` (test_evals).
- R2: `test_the_behaviour_case_reads_its_branch_and_says_it_ran`, rewritten.
- R3: `test_a_stop_case_keeps_every_never_write_grader`, `test_the_never_graders_match_what_they_forbid`, unchanged.
- R4: `test_a_failed_case_reruns_once_alone`.
- R5: `test_a_case_fails_only_twice`.
- R6: `test_a_rerun_the_cap_cant_cover_is_a_failure` (both causes).
- R7: `test_a_full_run_fails_a_case_on_two_runs`.
- R8: `test_a_trace_that_could_not_start_git_is_environment`, on `tests/fixtures/eval-trace-no-git.jsonl`.
- R9: `test_only_the_evals_own_workspace_is_removed` (portable), and a kept trace in the R4 test.
- R10: `test_the_run_reports_verdicts_and_its_note`, `test_a_runs_summary_reads_verdicts_or_its_result`.
- R11: `test_factory_cases_writes_the_note_ship_reads_or_stops`, turned around.
- R12: `test_factory_cases_skip_writes_why_and_runs_nothing`.
- R13: `test_a_failed_case_is_a_signal_not_a_refusal`.
- R14: `test_land_refuses_a_change_whose_checks_or_cases_havent_run`, extended to `ran` with failures and `skipped`.
- R15: `test_the_question_accepts_failed_or_skipped_cases_as_shown`.
- R16: `test_no_skill_grants_the_cases`; `test_land_runs_the_cases_before_its_question`.
- R15 (the dialog): `test_the_dialog_shows_each_failed_or_skipped_case`.
- R8 in a run: `test_a_sandbox_failure_is_never_rerun_nor_counted`; R5 in a run:
  `test_a_rerun_that_passes_passes_the_run`; R10's line: `test_the_runs_note_is_composed_once`.
- R17: `test_ship_cases_names_the_note_environment_and_rerun`.
- R18: `test_full_runs_are_kept_in_order`.
- R19: the acceptance check in `checks.md`.
- The pinned copy: `test_the_factorys_reading_of_case_failures_matches_sdlcs`.

## Rollback

`git revert` undoes it all. Nothing outside the repo is written by the code but run folders under
`.sdlc/reports/` (ignored) and the removal of the eval's own temporary `e-*` workspaces, which
`plugin eval` made and would otherwise leave; nothing restores those, and none is needed.
