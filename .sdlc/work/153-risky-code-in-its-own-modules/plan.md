---
id: 153
slug: risky-code-in-its-own-modules
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 153 — Close, push, the lock and the landing live in modules the deep review can name · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/closing.py` (new): the lock family, `cmd_close`, `_push`, `_push_plan`, and every
  name only they reach (R1, R3). Worked out by an AST closure over `sdlc.py`, seeded with R1's
  named entries: a top-level name moves when every statement that references it has moved. That
  takes close's helpers (`_close_commit`, `_drop_record`, `_handoff`, `_cleanup_plan`,
  `_carries_others`, `_ff_deletions`, `_merged_scripts`, `_reaches`, `register_plan`,
  `_without_entry`, `_branch_register_plan`, `_drop_commit`) and close's `measure` step
  (`measure_change`, `fix_trailers`, `_factory_files`, `_agent_sessions`, `_agent_models`,
  `_change_diff`, `_close_times`), plus `HANDOFF_ENV`, `RAN` and `CLEANUP_TIMEOUT`.
  `_project_dirs` stays: it is `metrics._project_dirs` bound at import, which the module can't
  read while loading (R5).
- **Constants, as built.** The closure moves functions; a constant moves only when it is named
  (R1/R2) or every statement in its commented block (no blank line between) moves too. A first
  pass moved constants by the closure alone and split families with one header comment: the
  `FACTORY_*` pinned copies in `sdlc.py`, `BASE_REF`/`BASE_KEY`, `FRESH_RE`/`CASES_RE` and
  `ENTRY_RE`/`ENTRY_ID_RE` in `factory.py`, each header landing on the wrong side. So those stay,
  read as `sdlc.<name>`/`factory.<name>`, and the pins they hold don't move. `RESOLVE_RECORDS`
  stays too: it is built at load from `COSTS`, `LAND_STEP`, `LAND_TIMES`, which stay (R5). The
  train's run block (`RUN_UNDER_WAY`, `RUN_EJECTS`, `RUN_STOPS`, `RERUN`, `PUT_BACK`) is named
  with `RUN_STEPS`, so the block moves whole, with the two `# ----` section headers above the
  train and its loop.
- `scripts/sdlc.py`: the moved definitions gone; `_load_closing()` beside `_load_retro()`;
  `closing = _load_closing()`; the few callers of R1's entries left here (`claim()`,
  `cmd_inbox_commit()`, the hand gate's `_unlock`, `cmd_release`, `cmd_publish`, `main()`) call
  `closing.<name>`.
- `plugins/factory/scripts/landing.py` (new): R2's commands and their state, and the names only
  they reach, by the same closure over `factory.py` (seeded with `cmd_land*`, `cmd_train`,
  `_train_*`, `_run_*` but `_run_check`, `run_lock`, `train_*`, `TRAIN_*`, `RUN_STEPS`,
  `cmd_resolve`, `_rebase_settling`, `cmd_land_verdicts`, `land_verdict`).
- `plugins/factory/scripts/factory.py`: the moved definitions gone; a `_Names` class and
  `_load_landing()`; `main()` dispatches to `landing.cmd_*`; whatever is left that names a
  seed calls it as `landing.<name>`. `landing.py`'s train runs `factory.FACTORY_SCRIPT` where
  it read `Path(__file__)`, and `land_question()`'s `moves` defaults to `None` (R5).
- `.sdlc/config.toml`: nothing; 158 put both paths under `[review] sensitive` on the base already.
- Tests: every reach of a moved name becomes `sdlc.closing.<name>` / `factory.landing.<name>`,
  `monkeypatch.setattr` targets included (R6); the source guards read the new modules (R8); new
  tests for R1–R5, R9 in `tests/test_modules.py` (new), R8's reach tests beside each guard
  (`test_sdlc.py`, `test_work_folder.py`, `test_skills.py`), R10 in `tests/test_factory.py`.
  The push guard now reads each core file apart: `_function()` slices to the next `def`, and
  joined, retro's last function ran on into `closing.py`'s docstring, which names `_push()`.
- Docs: AGENTS.md (*Modules loaded by path*, *Closing*, *The factory*, the push invariant),
  `docs/CONTRIBUTING.md` (*Layout*), `plugins/factory/README.md` where it places the landing.

The mover is a throwaway AST script outside the repo: it cuts each moved top-level statement
(with its decorators and the comment lines directly above it) into the module unchanged, and
prefixes each reference to a name that crossed the line (`sdlc.`/`factory.` in the module,
`closing.`/`landing.` in the script), judged by scope so a local of the same name is left alone.
`ruff check` (F821) catches any reference it missed on either side.

## Work order

1. **The tests that hold the line (red).** `tests/test_modules.py`: R1/R2 (definitions live in
   the module, not the script), R3 (the line rule), R4 (loaded by path, no import), R5 (nothing
   at load time), R9 (factory never loads `sdlc.py`), R8's guard reach test. All fail: the
   modules don't exist.
2. **`closing.py`.** Run the mover on `sdlc.py`, add `_load_closing()`, write the docstring,
   `ruff check`/`format`, then move every test reach of a moved name. R1, R3, R4, R5 for
   `closing` go green, then the suites that drive close, push and the lock (`test_archive`,
   `test_push`, `test_cleanup`, `test_register_lands`, `test_release`, `test_bugs`,
   `test_windows`, `test_train`'s lock tests) by name.
3. **Source guards (R8).** `closing.py` into `CORE` (`test_sdlc.py`, `test_work_folder.py`),
   the push guard's sources, `SCRIPTS` (`test_windows.py`); `landing.py` into `SCRIPTS`.
4. **`landing.py`.** Same steps on `factory.py`, with `_Names` and `_load_landing()` of its own,
   `land_question()`'s default made `None` (R5). R2, R3, R4, R5, R9 for `landing` go green, then
   `test_land`, `test_train`, `test_resolve`, `test_factory`, `test_board`, `test_hand_gate`.
5. **R10.** `test_the_landing_code_is_reviewed_in_depth` in `test_factory.py`.
6. **Docs (R12)** and the R7 `--help` comparison against the base.

## Tests

- R1, R2: `test_close_push_and_the_lock_live_in_closing`, `test_the_landing_lives_in_landing`.
- R3: `test_the_line_between_script_and_module_holds`, parametrized over both pairs.
- R4: `test_the_modules_are_loaded_by_path`; the existing stand-in tests (`setattr(factory,
  "_sdlc", …)`, `"_claude"`, `sdlc._git` fakes) passing unchanged show a stand-in reaches moved code.
- R5: `test_the_modules_read_nothing_while_loading`.
- R6, R7: the whole suite through the gate; `--help` of each named command diffed against the
  base's, recorded in the report's Evidence.
- R8: `test_the_source_guards_reach_closing_py`.
- R9: `test_the_factory_never_loads_sdlc_py`.
- R10: `test_the_landing_code_is_reviewed_in_depth` (`verdicts` full on either module, light on
  either script, `sdlc.risk_paths()` naming both modules and not `sdlc.py`).
- R11: the build's first `verdicts` (the factory's, not this builder's).
- R12: read by the reviewer; `sdlc.py context` lists the docs for ship.

## Rollback

`git revert` of the change's commit puts every function back where it was; nothing is written
outside the repo, no data format or trailer changes, and no host configures a moved name. The
`[review] sensitive` listing came in 158 and stays harmless if the modules go (it matches nothing).
