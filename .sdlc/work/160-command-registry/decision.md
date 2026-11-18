DECISION: READY

**Why.** All three reviewers passed round 2, and the full gate passed (`./check.sh`, exit 0, 2950 passed). The one change asked for in round 1 was made and checked: `Command` is now in `HELPERS`. Two behaviour checks against the merge base found the same help, usage errors and exit codes, and nothing in the reviews suggests the spec was wrong. The diff leaves `closing.py`, `retro.py`, `board.py` and `landing.py` alone, so it touches no sensitive path, push, secret or published interface.

**Open items**
- None. Round 2 was PASS from code, test and behaviour. Round 1's one change (test, C1: add `Command` to `HELPERS`) is fixed. Two nits remain. F1 (code) is marked minor. F3 (test) is recorded in `findings.md` and is not a change: `test_main_runs_a_stand_in_handler` passed before the move too, and stubs only `config`.

**Decisions to confirm**
- None. The folder has no `decisions.md`, so there is no blocking line and no open default.

**For the person at ship**
- **Check the diff is only this change.** Run `git diff main --stat` and confirm it lists only `scripts/sdlc.py`, `plugins/factory/scripts/factory.py`, `tests/test_registry.py` and the change folder. Two round-1 reviewers saw `test_function_heat.py`, `test_windows.py`, `.sdlc/config.toml` and `.sdlc/function-heat.py` there too. They took these for commits that reached `main` after the merge base, but neither confirmed it.
- **Read the two new `main`s and the helpers.** Check `UsageError`, `Command`, `arg`, `exclusive`, `command`, `_parser` and `HELP_ORDER` in both scripts against the spec's sketch. In `sdlc.py`, the own-script handoff must still run before parsing. In `factory.py`, the `change_root` step must still run before dispatch.
- **Run the acceptance check.** No reviewer ran the full "Help and usage errors match the base" check in `checks.md`. Each sampled part of it, and ship reruns it, so watch that it prints no `DIFF:` line.
- **One constant moved.** `STOPPED` now sits above `cmd_verdicts` in `factory.py`, with its value unchanged.

- IMPACT: none — this is a pure move. Every command's help, flags, defaults, output and exit codes match the base, so nobody holding the previous release does anything differently.

**Undone items**
- None. There is no `notes.md`, so there are no unticked items to dispose of.

**How to recover**
- The prompt names no irreversible paths. `plan.md`'s Rollback applies: `git revert` undoes the whole change.
