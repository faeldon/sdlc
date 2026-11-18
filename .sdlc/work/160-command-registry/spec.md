---
id: 160
slug: command-registry
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 160 — Each command registers itself, so adding one doesn't edit main · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

New tests go in `tests/test_registry.py`, marked `portable`: they read source or load the scripts, and run nothing.

1. **R1. Every subcommand's parser is built from the registry.** In `scripts/sdlc.py` and `plugins/factory/scripts/factory.py`, `add_parser`, `add_argument` and `add_mutually_exclusive_group` are called only inside the registry's builder, `_parser()`. `main` compares nothing against `args.cmd` and holds no string constant that names a registered command. Test: `test_every_parser_is_built_by_the_registry` (AST, both scripts). It fails if a parser or a dispatch branch is added anywhere else, so `main` can't grow back.
2. **R2. Each command is declared beside its handler.** A command's declaration is its name, help, arguments and handler. Where the command's adapter calls exactly one `cmd_*` function defined in the same script, the adapter is the next top-level function after that `cmd_*`. Test: `test_each_command_sits_beside_its_handler`.
3. **R3. `--help` is byte-identical.** This covers the top-level help of both scripts and the help of every command. Order, wording, metavars, choices and exit code all match the base branch. Check: the acceptance check in *Verification* compares the base's copy with the change's copy and prints no diff.
4. **R4. Usage errors and refusals before a handler runs are byte-identical, exit code included.** Cases:
   - an unknown command
   - a missing required argument (`sdlc.py ship`, `factory.py start 1`)
   - a bad choice (`sdlc.py new x --tier 3`)
   - two flags from one mutually exclusive group (`sdlc.py resolve --continue --abort`)
   - `sdlc.py cases compare` with no run
   - `sdlc.py preflight 001 --nits` without `--question`
   - `factory.py land 001` without `--by`
   - `factory.py` with no command

   Check: the same acceptance check. The suite keeps covering the preflight case (`tests/test_preflight.py`, `main() == 1`).
5. **R5. The default is unchanged.** `sdlc.py` with no command runs `status`, which reads `--all` as false. `factory.py` with no command is a usage error (exit 2). Check: the acceptance check, plus the existing `status` tests, which call `sdlc.main()`.
6. **R6. `main`'s steps before dispatch run in the same order as today.**
   - `sdlc.py`: `_utf8_streams()`, then the own-script handoff for `OWN_SCRIPT_CMDS` before parsing, then `repo_root()`, then `main_root()`.
   - `factory.py`: `_utf8_streams()`, parsing, `repo_root()`, then `change_root()` whenever the parsed namespace has a truthy `id`.

   Check: the existing handoff tests (`tests/test_evals.py`, `tests/test_hand_gate.py`) and the factory tests that reach a change's worktree pass unchanged.
7. **R7. Handlers are reached live.**
   - An adapter calls its handler through the script's globals when it runs, so a stand-in a test sets on the script is what `main()` runs.
   - `test_status_never_loads_the_board` passes unchanged: `board`'s adapter keeps the literal line `return _load_board().cmd_board(root, args.port)`, and it is still the only `_load_board()` call.
   - New test: `test_main_runs_a_stand_in_handler`, which monkeypatches one `cmd_*` on each script and asserts `main()` returned what the stand-in returned.
8. **R8. The modules' commands are registered by the scripts.** `sdlc.py` registers `close`, `retro`, `retro-commit` and `board`, and its adapters call `closing.cmd_close`, `retro.cmd_retro`, `retro.cmd_retro_commit` and `_load_board().cmd_board` when they run. `factory.py` registers `land`, `land-check`, `train`, `resolve`, `land-verdicts` and `land-fix`, whose adapters call `landing.*`. `scripts/closing.py`, `scripts/retro.py`, `scripts/board.py` and `plugins/factory/scripts/landing.py` are not in the diff. Check: `tests/test_modules.py` passes unchanged, and `git diff main --stat` lists none of the four.
9. **R9. The permission lists keep their values and order.** `READ_ONLY`, `ALLOW_RULES` and `OWN_SCRIPT_CMDS` hold the same entries in the same order as today. New test: `test_the_permission_lists_name_registered_commands`, which asserts every name in the three is a registered command. The existing checks keep `board` out of `READ_ONLY` and `ALLOW_RULES`, and `run-cases` out of `ALLOW_RULES`; they pass unchanged (`tests/test_readiness.py`, `tests/test_skills.py`, `tests/test_acceptance.py`, `tests/test_hand_gate.py`).
10. **R10. A name registered twice fails when the script loads**, with an error naming the command. Test: `test_a_command_registered_twice_is_refused`, which calls the registry's `command()` twice with one name on a freshly loaded script.
11. **R11. The top-level help order is pinned in one place, `HELP_ORDER`.** Each script has this tuple, outside `main`, holding today's order. A registered command not named in it follows the named ones, in the order it was registered, so adding a command needs no edit there. Test: `test_help_order_names_only_registered_commands`. It asserts `HELP_ORDER` has no duplicates and that each name in it is registered. It does not require every registered command to be listed.
12. **R12. The two copies of the registry helpers are pinned identical.** The helpers are `arg`, `exclusive`, `command` and `_parser`. `factory.py` never imports `sdlc.py`, so the copies are pinned by test, as `_utf8_streams` is. Test: `test_the_registry_copies_match` compares the helpers' source in the two scripts.
13. **R13. Pure move.** No command, flag, default, alias or shim is added or removed. Existing tests change only in how they reach a moved name; today that is none, since no test calls an adapter. Check: `./check.sh` is green, and `git diff main --stat -- tests/` lists only `tests/test_registry.py` plus any reach-only edits.

## Design

### Taken as given (checked in the code)

- `sdlc.py`'s `main` runs from line 9482 to line 9957 (476 lines). It builds 45 subparsers with `sub = ap.add_subparsers(dest="cmd")`, which is not required, and routes them with an `if args.cmd == …` chain. `check` and the default `status` share an `analyze(root)` tail.
- `factory.py`'s `main` runs from line 5452 to line 5635. It uses `add_subparsers(dest="cmd", required=True)`. One branch is cross-cutting: `if getattr(args, "id", None): root = change_root(root, args.id)`. `cmd_stage` is reached by falling through the chain. The `agent` parser gets `--decision`, `--revise` and `--recheck` after the `land-fix` parser, which only affects where the code sits: argparse keeps `agent`'s own argument order (id, `--task`, `--role`, `--decision`, `--revise`, `--recheck`).
- No test introspects either parser (no `--help` or parser reads in `tests/`). Tests reach `main` through `sdlc.main()` with a patched `sys.argv`. The only stand-in set on a dispatch target is `_load_board` (`tests/test_board.py:2928`).
- `tests/test_modules.py`'s `test_the_modules_read_nothing_while_loading` forbids `closing.py` and `landing.py` from reading their binding while they load, and the binding is unset at that point (`mod.sdlc = …` comes after `exec_module`). That rules out a decorator in either module.
- Some help strings and choices read module constants (`TRIAGE_VERDICTS`, `WORKTREES_LINE`, `STARTS`, `TASKS`, `REVIEWERS`, `UI_REVIEWERS`, `REPORT_KINDS`, `STOPPED`, `LAND_STEP`, `CONFIG_FILE`). A declaration evaluates them where it sits. `STOPPED` (`factory.py:3410`) is defined after `cmd_verdicts` (`:2285`), so one constant must move up.
- The `--help` output the person sees is mostly the top-level listing, whose order is the order the subparsers are added.

### The registry (one copy in each script, near the top, before the first command)

- `arg(*names, **kwargs)` records one `add_argument` call, unevaluated.
- `exclusive(*args, required=False)` records one mutually exclusive group and the arguments in it.
- `command(name, about, *specs)` is a decorator. It records the decorated adapter, the help and the specs under `name` in the module's own `COMMANDS` dict, raises `ValueError` if `name` is already there (R10), and returns the adapter unchanged.
- `_parser(description, required)` builds the `ArgumentParser` and its `add_subparsers(dest="cmd", required=required)`. It adds each command named in `HELP_ORDER`, then every other registered command in registration order, applying each spec in its recorded order: a group becomes `add_mutually_exclusive_group(required=…)` with its arguments added inside it. This is the only place the three argparse builder calls appear (R1).

`COMMANDS` is a module-level global, so each load of a script by path, as the tests do under several module names, gets its own registry.

### Adapters

- Each command has one adapter, `cli_<name>` with hyphens turned to underscores (`cli_inbox_commit`), decorated with `@command(...)`. The adapter's body is exactly the dispatch code moved out of `main`: `ship`'s `--fixed` split, `preflight`'s `--question` fork and refusal, `resolve`'s mode, `run-cases`'s `--full`, `factory land`'s `--by` refusal and `--close` fork.
- The `cli_` prefix avoids `factory.py`'s existing `_run_check` and `landing.py`'s `_run_*`.
- Signatures: `sdlc.py`'s adapters take `(root, home, args)`; `factory.py`'s take `(root, args)`.
- Calls go to `cmd_*` through the global name, so stand-ins reach them (R7).
- Each adapter sits directly after the `cmd_*` it calls (R2).
- Adapters with no single `cmd_*` sit beside the code they run:
  - `cli_next` beside `next_id`
  - `cli_next_entry` beside `next_entry_ids`
  - `cli_check` and `cli_status` beside `print_status`; `cli_status` is `main`'s status tail moved verbatim, `getattr(args, "all", False)` included
  - `cli_cases` beside `cmd_cases_compare`
- The four whose handlers live in loaded modules (`close`, `retro`, `retro-commit`, `board`) sit in `sdlc.py` after `closing = _load_closing()` and `_load_board`. `factory.py`'s six landing adapters sit after `landing = _load_landing()`. None of those modules changes (R8).
- `cases compare` with no run currently calls `ap.error(…)` on the top-level parser. Its adapter raises a small `UsageError` instead. `main` catches only that exception and calls `ap.error(str(e))`, which prints the same usage and message and exits 2 (R4). `UsageError` is part of the copied helpers.
- `METRICS_HELP` becomes a module constant in place of `main`'s local `metrics_help`.
- `STOPPED` moves above `cmd_verdicts`, unchanged. This is the only constant that has to move. If the build finds another declaration that evaluates a constant defined after it, it moves that constant up the same way, never changing its value.

### `main` after the change

`sdlc.py`:

```python
def main() -> int:
    _utf8_streams()
    ap = _parser(
        "Track the change artifacts under .sdlc/work/ (see the repo's process doc).", False
    )
    if len(sys.argv) > 1 and sys.argv[1] in OWN_SCRIPT_CMDS and (own := _own_script(repo_root())):
        code = _run_own(own, sys.argv[1:])
        if code is not None:
            return code
    args = ap.parse_args()
    root = repo_root()
    home = main_root(root)
    run = COMMANDS[args.cmd].run if args.cmd else cli_status
    try:
        return run(root, home, args)
    except UsageError as e:
        ap.error(str(e))
```

`factory.py` is the same, with `required=True`, no handoff and no `home`, and its `change_root` step kept before dispatch.

### Edge cases

- **Duplicate name.** Refused when the script loads (R10).
- **A `HELP_ORDER` name with no command.** Fails the R11 test.
- **A new command.** It needs only its adapter and declaration. It appears at the end of the top-level help until someone deliberately adds it to `HELP_ORDER`.
- **`--help` for a command in `OWN_SCRIPT_CMDS` from a change's worktree.** It still hands off before parsing, as today.

### Boundaries

- **Always:** keep every command's output and exit code; keep `main`'s pre-dispatch order; keep the modules untouched.
- **Ask first:** reordering the top-level help; deriving `READ_ONLY` or `OWN_SCRIPT_CMDS` from the registry; touching `closing.py` or `landing.py`.
- **Never:** a new command, flag, alias or shim; changing a `cmd_*` signature; editing `AGENTS.md`, `docs/` or a skill. The helpers' docstrings are the registry's contract, and no map line in `AGENTS.md` stops being true.

## Contracts touched

- **Modules loaded by path** (*Modules loaded by path*, `tests/test_modules.py`). The rule is that a module is loaded by path, bound to a live view, and reads nothing while it loads. No module registers anything. The scripts declare the modules' commands, and their adapters reach `closing.`, `retro.`, `landing.` and `_load_board()` only when called. `closing.cmd_close` and the `landing.cmd_*` are already named entries, so the "stayed" and "should move" checks hold.
- **`factory.py` never imports `sdlc.py`.** Each script has its own copy of the helpers, pinned identical (R12), like `_utf8_streams`.
- **Only the named steps push.** `_push()` and its callers are untouched, and `close` still dispatches to `closing.cmd_close`.
- **`board` stays out of `READ_ONLY` and `ALLOW_RULES`, and `run-cases` out of `ALLOW_RULES`.** The lists are unchanged (R9). The board's single `_load_board()` call and its literal line are kept (R7).
- **Narrow `allowed-tools`.** No command line a skill runs changes, so every `Bash(...)` rule still matches.
- **The scripts run on Windows.** Nothing new is imported, and `argparse` is already imported at the top. No subprocess call or file write is added.
- **`test_no_git_call_names_main_itself`.** No string constant `main` is added.
- **Script dependencies.** Nothing new; `argparse` is in the standard library.
- **`[review] sensitive`.** The design keeps `closing.py` and `landing.py` out of the diff (R8), so the review is not forced to full depth by path. If the build finds it can't, it must stop and say so; it should not edit them quietly.

No invariant needs to change.

## Alternatives rejected

- **A central table of every command's declaration.** It moves the hot spot from `main` to the table: every change to any command would still edit the same few hundred lines, and a train would still conflict there.
- **Decorating `cmd_*` directly.** It would either change their signatures, which tests call positionally, or need a mapping from parameter names to `args` that hides the dispatch. It would also store the function object, so a stand-in set on the script would no longer reach `main`.
- **Each module registering its own commands.**
  - A decorator in `closing.py` or `landing.py` would read its binding while loading, which `test_the_modules_read_nothing_while_loading` forbids, and the binding is unset at that point anyway.
  - Exporting plain data from the modules would work, but it touches two sensitive files for no behaviour.
- **Deriving `READ_ONLY` and `ALLOW_RULES` from a flag in the registry.** The derived order would follow registration or `HELP_ORDER`, not today's `READ_ONLY` order. That order is what setup writes into a host's `.claude/settings.json` and what `readiness` prints as `missing`, so a derived list is not a pure move. Keeping the lists and checking them against the registry (R9) gives the same safety.
- **Help order from the order adapters appear in the file.** This removes `HELP_ORDER`, but it reshuffles the top-level help, which the intent forbids.
- **Golden `--help` snapshots in the suite.** Every future help edit would rewrite one shared file, which recreates the conflict. The equivalence is proved once, by an acceptance check (`acceptance()` checks are never rerun by a later change).
- **A shared registry file loaded by both scripts.** `factory.py` reads nothing of `sdlc`'s, and the factory's cached copy doesn't sit beside `scripts/`. Pinned copies are the repo's existing answer.
- **`set_defaults(func=…)` per subparser.** It works, but it adds a key to every namespace that nothing needs. `COMMANDS[args.cmd]` is the plainer lookup.

## Verification

1. `./check.sh`. Healthy: `ruff check` and `ruff format --check` are clean, `pytest -n auto` passes with the new `tests/test_registry.py` tests among them, and `claude plugin validate --strict` passes.

2. `uv run --group dev pytest -q tests/test_registry.py tests/test_modules.py tests/test_board.py::test_status_never_loads_the_board`. Healthy: all pass.

3. The acceptance check (R3, R4, R5), written into `checks.md` and run once through `sdlc.py accept`. It runs from the worktree and writes only under a temp dir:

   ```bash
   export SDLC_OWN_SCRIPT=off
   tmp=$(mktemp -d)
   git archive "$(git merge-base HEAD main)" scripts plugins/factory/scripts | tar -x -C "$tmp"
   for s in scripts/sdlc.py plugins/factory/scripts/factory.py; do
     cmds=$(uv run --quiet --script "$tmp/$s" --help | sed -n 's/^usage:.*{\([^}]*\)}.*/\1/p' | tr , ' ')
     for c in "" $cmds; do
       diff <(uv run --quiet --script "$tmp/$s" $c --help 2>&1; echo "exit $?") \
            <(uv run --quiet --script "$s" $c --help 2>&1; echo "exit $?") || echo "DIFF: $s $c"
     done
   done
   ```

   The same `diff` pattern then runs over the R4 error cases: `nosuch`; `ship`; `new x --tier 3`; `resolve --continue --abort`; `cases compare`; `preflight 001 --nits`; `factory.py` with no command; `factory.py start 1`; `factory.py land 001`.

   Healthy: no `DIFF:` line and no diff output. Each `exit` line matches: 0 for help, 2 for usage errors, 1 for the two refusals.

4. `git diff main --stat`. Healthy: it lists `scripts/sdlc.py`, `plugins/factory/scripts/factory.py`, `tests/test_registry.py` and the change folder, and none of `scripts/closing.py`, `scripts/retro.py`, `scripts/board.py` or `plugins/factory/scripts/landing.py`.

5. `grep -c 'args.cmd ==' scripts/sdlc.py plugins/factory/scripts/factory.py`. Healthy: `0` for both.

