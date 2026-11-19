---
id: 171
slug: factory-run-state
kind: plan
created: 2026-11-19
updated: 2026-11-19
---

# 171 — The factory's run state lives in a module of its own · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/run_state.py` (new): the docstring the spec's Design names,
  `factory = None`, and the moved functions in their order in `factory.py` today (`reworked`,
  `_untouched`, `settled`, `decision_preamble`, `loop_state`, `early_stop`, `cheap_nits`,
  `read_gate`, `_gate_state`), each body the base's with every name `factory.py` keeps read as
  `factory.<name>`. `decision_preamble` is a ninth the spec's list missed: only `loop_state`
  calls it, so R3's rule moves it (found by R3's test; `notes.md`, and a default decision).
- `plugins/factory/scripts/factory.py`: the nine definitions removed; `_load_run_state()` beside
  `_load_landing()` (a copy with the module's name and file), `run_state = _load_run_state()` right
  after `landing = _load_landing()`; `cmd_verdicts`, `cmd_upgrade` and `cmd_agent` call
  `run_state.loop_state(...)`. Nothing else: the constants, `read_gate_file`, `gate_path`,
  `build_round`, `_change_path`, `read_snapshot`, the record writers and `cmd_verdicts` stay.
  Checked by grep: no other code in `factory.py` or `landing.py` names a moved function
  (`landing.py` names `loop_state` once, in a comment, and has its own `_land_gate_state`).
- `plugins/factory/scripts/landing.py`: -80's guard in `cmd_land_fix` (`.is_dir() and any(...)`),
  -69's comment above `_run_loop()`. Nothing else.
- `tests/test_modules.py`: `RUN_STATE_PY`, `RUN_STATE_NAMES`, the `run_state` case in every
  parametrised rule (lives-in, line, loaded-by-path, read-nothing-while-loading, never-loads-sdlc),
  the pair's siblings (`[LANDING_PY]` and `[RUN_STATE_PY]`), `factory.run_state.factory` in
  bound-live, and two new tests: `test_the_run_state_lives_in_run_state` (R1 by name, plus R7's
  names staying in `factory.py`) and `test_run_state_defines_no_constant` (R4).
- `tests/test_factory.py`: re-point `factory.loop_state` → `factory.run_state.loop_state` and
  `factory.read_gate` → `factory.run_state.read_gate` (17 sites, R7's source check among them);
  R15's marks and docstrings on 155's five check tests. No assertion changes.
- `tests/test_land.py`: `test_a_fix_asked_with_its_land_round_folder_gone_is_not_a_traceback` (R9).
- `tests/test_train.py`: R11's last-id stack test, R12's labelled `refused`, R13's four stop
  tests, R14's monotonic deadline, R17's Windows kill test, its body a helper
  (`_killed_at_its_gate()`) that a POSIX twin also runs, so the path is shown off Windows too.
- `tests/test_board.py`, `tests/test_prompts.py`: no diff (neither names a moved function).
- `.sdlc/work/171-factory-run-state/notes.md`: -68's answer (R16).

## Work order

1. **The module, by a mechanical move.** Write the failing `test_modules.py` cases first (R1–R4,
   R7, R8), see them fail on the missing file, then cut the eight functions out of `factory.py`
   with a one-off script that copies each span verbatim and prefixes, by AST, every load of a name
   that is a `factory.py` global (not a parameter, local, builtin, import or moved function) with
   `factory.`; add the loader and re-point the three call sites and the tests' 17. Green:
   `tests/test_modules.py`, then the five files R6 names, by file. Check R5 with
   `git diff --color-moved=zebra`.
2. **-80 (R9).** The test first, red with `FileNotFoundError`; then the guard.
3. **-69 (R10).** The comment.
4. **-84, -85 (R11, R12).** The last-id stack test (`_conflicting(...)` with each change's own
   `.sdlc/last-id` from `sdlc.py new` already conflicting on stacking: shown red by making
   `_stray` see the counter, then reverted), and `refused(label, stray)`.
5. **-70 (R13).** Four tests over `_run_loop` with `_run_one`/`_run_group` stubbed on
   `factory.landing`; each shown red by taking its stop out by hand, then put back.
6. **-71 (R14), -98 (R15).** The kill test's deadline; the marks and docstrings.
7. **Idea -67 (R17).** The Windows kill test, skipped here.
8. **-68 (R16).** `notes.md`.

## Tests

- R1, R7: `test_the_named_code_lives_in_its_module[run_state]`, `test_the_run_state_lives_in_run_state`.
- R2: `test_the_modules_are_loaded_by_path[run_state]`, `test_the_modules_are_bound_live`,
  `test_the_modules_read_nothing_while_loading[run_state]`.
- R3: `test_the_line_between_script_and_module_holds[run_state]` and `[landing]` with the new siblings.
- R4: `test_run_state_defines_no_constant`.
- R5: by reading the moved diff (`git diff --color-moved=zebra <base> -- plugins/factory/scripts/`):
  the code review's first check.
- R6: `tests/test_factory.py`, `test_prompts.py`, `test_board.py`, `test_land.py`, `test_train.py`
  pass with only call sites re-pointed; `test_loop_state_reads_no_step_record` on the moved source.
- R8: `test_the_factory_never_loads_sdlc_py[run_state.py]`.
- R9: `test_a_fix_asked_with_its_land_round_folder_gone_is_not_a_traceback`.
- R10: by reading `landing.py` above `_run_loop()`: the review checklist's second item.
- R11: `test_a_stack_conflicting_on_last_id_too_resolves`.
- R12: `test_a_resolution_outside_its_files_is_refused`, its messages carrying the label.
- R13: `test_train_run_stops_at_a_failed_step`, `test_train_run_stops_at_an_agents_problem`,
  `test_train_run_stops_at_a_resolve_with_no_conflict`, `test_train_run_stops_at_the_trains_stop`.
- R14: `test_a_killed_train_run_resumes`, by reading its wait: a `time.monotonic()` deadline of 120 s (not the spec's 60 s, which the loop's startup outran under load in round 1), polled every 0.05 s.
- R15, by reading: `test_two_checks_with_one_slot_run_one_after_the_other`,
  `test_a_check_waits_for_a_gates_slot` and
  `test_a_green_check_writes_nothing_and_never_clears_the_gate` get `portable` (Python stamps and
  holds, `sh` commands with no kill, which Git for Windows' `sh` runs as `test_acceptance.py`'s
  portable checks do); `test_a_killed_check_frees_its_slot` (`start_new_session`/`killpg`) and
  `test_a_check_past_the_timeout_is_killed` (the kill of an `sh`'s `exec sleep`) get a docstring
  sentence.
- R16: `notes.md`.
- R17: `test_a_killed_train_run_resumes_on_windows`, skipped off Windows (runs on CI's Windows
  job); `test_a_train_run_killed_at_its_gate_resumes` runs the same body here with `killpg`.
- R18: `git diff --stat` against the base.

## Rollback

`git revert` undoes all of it: the change writes no data, publishes nothing and renames nothing a
host reads (the module is loaded by path inside the factory; `verdicts`' JSON is unchanged).
