---
id: 160
slug: command-registry
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 160 — Each command registers itself, so adding one doesn't edit main · plan

> Written after reading both `main`s (`sdlc.py:9482`, `factory.py:5452`), the tests that reach
> them (`tests/test_board.py::test_status_never_loads_the_board`, `tests/test_preflight.py`,
> `tests/test_windows.py`'s pinned copies) and `tests/test_modules.py`.

## Files to change

- `scripts/sdlc.py`: the registry helpers (`UsageError`, `COMMANDS`, `arg`, `exclusive`,
  `command`, `_parser`) and `HELP_ORDER` before the first command (above `cmd_config`); one
  `@command` `cli_<name>` adapter after each handler; `METRICS_HELP` a module constant; `main`
  cut to parse, hand off and dispatch.
- `plugins/factory/scripts/factory.py`: the same helpers, a copy pinned identical; its own
  `HELP_ORDER`; one adapter per command; `STOPPED` moved above `cmd_verdicts`, unchanged; `main`
  cut the same way, keeping the `change_root` step.
- `tests/test_registry.py` (new): the R1, R2, R7, R9, R10, R11, R12 tests, marked `portable`.
- `.sdlc/work/160-command-registry/checks.md` (new): the byte-identical help and errors check
  (R3, R4, R5) against the merge base, and the modules-not-in-the-diff check (R8).
- Not touched: `scripts/closing.py`, `scripts/retro.py`, `scripts/board.py`,
  `plugins/factory/scripts/landing.py`, any existing test, any skill or doc.

Reused, not re-derived: every `cmd_*` as it is (no signature changes), `_own_script`/`_run_own`,
`repo_root`, `main_root`, `change_root`, `emit`, `next_id`, `next_entry_ids`, `analyze` and the
status tail moved verbatim.

## Work order

1. **Tests first.** `tests/test_registry.py` with every R-test; run it: all fail (no `COMMANDS`,
   no `_parser`, `main` full of `add_parser`).
2. **Slice: `sdlc.py`.** Helpers and `HELP_ORDER` at the top; each adapter moved beside its
   handler (the module commands after `closing = _load_closing()` / `_load_board`); `main`
   reduced. Run the sdlc half of `test_registry.py`, `tests/test_board.py::test_status_never_loads_the_board`,
   `tests/test_preflight.py`, `tests/test_modules.py`, and the help/error diff against the base.
3. **Slice: `factory.py`.** The copied helpers, its adapters (landing ones after
   `landing = _load_landing()`), `STOPPED` moved up, `main` reduced. Run the rest of
   `test_registry.py`, `tests/test_windows.py`, and the help/error diff.
4. **`checks.md`** written and run once by hand from the worktree.

## Tests

- R1: `test_every_parser_is_built_by_the_registry` (AST over both scripts: the three builder
  calls only in `_parser`; `main` has no `args.cmd` comparison and no string naming a command).
- R2: `test_each_command_sits_beside_its_handler` (AST: an adapter calling exactly one local
  `cmd_*` is the next top-level function after it).
- R3, R4, R5: `checks.md`'s *Help and usage errors match the base*, a diff of every command's
  `--help` and each listed error case against the merge base's scripts, exit codes included.
- R6: existing handoff tests (`tests/test_evals.py`, `tests/test_hand_gate.py`), unchanged.
- R7: `test_main_runs_a_stand_in_handler` (both scripts) and the unchanged
  `test_status_never_loads_the_board`.
- R8: `tests/test_modules.py` unchanged; `checks.md`'s *The loaded modules are not in the diff*.
- R9: `test_the_permission_lists_name_registered_commands`; existing list tests unchanged.
- R10: `test_a_command_registered_twice_is_refused`.
- R11: `test_help_order_names_only_registered_commands`.
- R12: `test_the_registry_copies_match`.
- R13: the gate, with `git diff --stat -- tests/` showing only `tests/test_registry.py`.

## As built

- The helpers gained a small `Command` class (the adapter, help line and specs `COMMANDS`
  holds), pinned with the others by `test_the_registry_copies_match`.
- `STOPPED` moved above `cmd_verdicts` with a one-line comment; its old comment stays over
  `STOPPED_RE`. Its value is unchanged (`tests/test_metrics.py`, `tests/test_board.py` compare it).
- `METRICS_HELP` sits just above `cmd_unreleased`, its first reader.
- `test_main_runs_a_stand_in_handler` passed before the move too: it guards R7 rather than
  driving it, since `main` already reached handlers by global name.
- `ruff format --check` reads Python blocks in Markdown: the `main` sketch in `spec.md` (and its
  copy `runs/spec-draft.md`) had a line over 100 columns, which failed the gate; ruff rewrapped
  that one call, no word changed.

## Rollback

`git revert` undoes all of it: nothing is written outside the repo, no data format, config key,
command line or published artifact changes.
