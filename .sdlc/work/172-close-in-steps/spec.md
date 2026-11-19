---
id: 172
slug: close-in-steps
kind: spec
created: 2026-11-19
updated: 2026-11-19
---

# 172 — Close runs as named steps · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions checked in the code. `cmd_close` (`scripts/closing.py`, lines 708–1076) already names its steps, but as eleven closures inside one function: `merge`, `verify`, `measure`, `mirror`, `remove_folder`, `tell_issues`, `record`, `git_step`, `delete_branch`, `push` and `cleanup`. Each one reads about fifteen of the function's locals. Before those closures it runs about 140 lines of refusals and previews. The step names the report shows (`"merge"`, `"remove folder"` and so on) are output, and the tests assert them. Tests replace `measure_change`, `_handoff`, `_push_plan`, `_lead_line`, `CLEANUP_TIMEOUT` and `datetime` on `sdlc.closing`, so the moved code must look these up as module globals each time it runs.

R1. `cmd_close` defines no nested function, and its body, docstring excluded, is at most 40 lines. A new test, `test_close_is_a_sequence_of_named_steps` in `tests/test_modules.py`, reads `closing.py`'s AST and fails on a nested `def` or a longer body.

R2. No function in `scripts/closing.py` is longer than 100 lines, docstring included. The same test checks every top-level function and fails on any longer one.

R3. Each step is a top-level function in `closing.py`: `_step_merge`, `_step_verify`, `_step_measure`, `_step_archive`, `_step_remove_folder`, `_step_tell_issues`, `_step_record`, `_step_remove_worktree`, `_step_delete_branch`, `_step_push` and `_step_cleanup`. The same goes for the stages around them: `_close_target` (finds the change), `_close_refusals`, `_close_preview` (start ref, cleanup plan, deletions, reach, push plan), `_close_steps` (the list for a kind) and `_run_close_steps` (the loop, the lock and the handoff after the merge). Every one of these names is added to `CLOSING_NAMES` in `tests/test_modules.py`, so `test_close_push_and_the_lock_live_in_closing` fails if one moves into `sdlc.py`.

R4. Nothing a person sees changes. Before the move, in the change's first commit, a characterization test `test_close_output_is_unchanged` (new, in `tests/test_archive.py`) pins five scenarios against the old code:

- a shipped close
- a dropped close
- `close --check` on a shipped change
- a rerun after an archive that failed
- a shipped close with `git.push = ["close"]` against a bare remote

For each one it pins three things: the report's JSON text (key order included, with temp paths and short shas normalised), the exit code, and the newest commit's subject, trailers (the clock-dependent values of `Sdlc-Totals`/`Sdlc-Lead` normalised) and tree. The same test passes unchanged after the move. It fails if a key moves, a step is renamed, or a trailer or commit differs.

R5. Every existing test of close passes with no edit beyond R3's `CLOSING_NAMES` addition and R7's new case:

- `tests/test_archive.py`, `test_cleanup.py`, `test_push.py`, `test_register_lands.py`
- `tests/test_train.py`, `test_land.py`, `test_adoption.py`, `test_metrics.py`, `test_board.py`
- `tests/test_evals.py`, `test_config_resolution.py`, `test_resolve.py`, `test_sdlc.py`, `test_retro.py`, `test_readiness.py`

A diff of `tests/` showing other edits fails review.

R6. Refusing and resuming are exactly as today:

- The git steps are `merge --ff-only`, `worktree remove` without `--force` and `branch -d`.
- The lock is taken right before the first step. It is let go after `remove folder` (or `record`, for a drop) and before the worktree is removed.
- `tell_issues` runs after the lock is let go.
- When a close runs from inside the worktree, the `remove worktree` step returns exit 3.
- When the merge brings changes under `scripts/`, the merged code takes over through `_handoff()`.
- A refused push is `push_failed`, and a failed cleanup is `cleanup_failed`.

The existing tests that pin each of these (in `test_archive.py`, `test_push.py` and `test_cleanup.py`) are the check. R4's rerun scenario covers resuming.

R7. Nit 2026-11-19-4: a change whose `opened:` parses but is later than the close gets no `Sdlc-Lead` line, and its `Sdlc-Coverage` ends with ` lead=bad-opened`. New test: `test_a_change_opened_after_its_close_says_bad_opened` (`tests/test_archive.py`). It freezes `closing.datetime` with `_Frozen` and sets `opened` after it. It asserts that `opened_at()` returns a datetime, so this is decision D3's path and not the malformed-value case, and that the close lands with every other trailer.

R8. Nit 2026-11-19-3: when timing the lead time raises, the trailers stay exactly as today (` lead=failed`, no `Sdlc-Lead`). Close's report adds `measure.errors`, a list holding `"lead: <TypeName>: <message>"` with the message cut to 200 characters. The key appears only when something failed, so a healthy close's report is unchanged (R4). `test_timing_that_fails_drops_only_its_own_line` gains this assertion: `out["measure"]["errors"] == ["lead: RuntimeError: a run file shape nobody planned for"]`. Without the fix, that assertion fails.

R9. Nit 2026-11-18-100: the cost ceiling for a rerun is the cap less what has been spent, rounded down to whole cents, with float noise below a millionth of a dollar ignored first. Spending 0.65 leaves `4.35`, not `4.34`. New test: `test_the_rerun_ceiling_keeps_its_last_cent` (`tests/test_evals.py`). It uses a first run that costs 0.65 and asserts `--max-cost-usd` is `"4.35"`. A second case asserts that 0.30000000000000004 leaves `"4.69"`, so the result still rounds down and never up. The existing `"3.75"` assertion in `test_a_failed_case_reruns_once_alone` still holds.

R10. Nit 2026-11-19-2 is retired as answered. No code changes for it, and a factory change with neither timed rows nor transcript events still gets no `ready_wait`. Ship retires all four nits in the change's `entries.md` with `Retire <id>: <reason>` lines (-2's reason: answered by 162's D1). `sdlc.py check` reads them through `held_entries()`. The register is never edited on the branch.

R11. The handoff still works between versions. In this repo, main's old script runs this close and hands it to the merged new script partway through. The command line `close <branch> [--check]`, `HANDOFF_ENV`, `LOCK_HELD_ENV` and the JSON report on stdout stay as they are. `tests/test_adoption.py`, which runs a full `new`-to-`close` through `uv run --script`, passes.

R12. Every Windows rule still holds (`tests/test_windows.py` passes). The move adds no subprocess call, no text write and no module that only exists on one platform.

R13. `closing.py`'s module docstring and `cmd_close`'s docstring name the step functions and the state object. AGENTS.md's *Closing* paragraph is still true and is not edited.

R14 (ask first). Change the sentence in `docs/REFERENCE.md` §Metrics that says a `source=git` line "holds `lead` and `ready_wait` (with `landing` for a factory change)". The new text: a factory change's `source=git` line holds `lead` and `landing`, because without an approver row nothing says when it was ready. Then the docs agree with the code that -2 accepts. This is a docs-only edit, and no test is needed.

## Design

**State object.** `_Close`, a `@dataclass` defined at module level in `closing.py`. It holds what the closures share today:

- Settings and context: `main`, `tree`, `branch`, `folder`, `kind`, `trunk`, `cfg`, `own_repo`, `unavailable`, `check_only`.
- Refs and plans: `sha`, `start` (the base ref), `plan` (the push plan), `wipe` (the cleanup plan).
- Shared output: `report`, `kept` (the drop's reached/reason), `captured` (the measure trailers).

Each step is `def _step_x(c: _Close) -> str | None`: an error string, or None. `push` and `cleanup` return None, as today. Steps read and write `c.report` in the same order the closures did. JSON key order is insertion order, so R4 depends on that.

**One accidental fix.** Today line 885 rebinds the local `own` from "this is the plugin's repo" (a bool) to the list of unpushed commits, and line 1066 reads `own` again. The two fields are kept apart now. This changes no behavior:

- In a host repo, `_merged_scripts()` is false whatever `own` holds, because it compares `PLUGIN_DIR` to `main`.
- In this repo, the list is non-empty whenever the merge moves anything. When the merge moves nothing, `_merged_scripts()` sees `before == after` and is false.

Inside `delete_branch`, the locals that shadow `kind` and `kept` get their own names.

**The sequence:**

```
cmd_close(root, ident, check_only):
    held = pop LOCK_HELD_ENV; main = main_root(root); _inherit_lock(main, held)
    own-repo handoff to main's script                      # unchanged, first
    c = _close_target(root, main, ident, check_only)       # report skeleton, archive refusal, find the change
    if c.report["refusals"]: return _emit(c.report, 1)
    if _close_refusals(c): return _emit(c.report, 1)       # stage, dirty trees, trunk, ff, train, register
    _close_preview(c)                                      # start ref write (not --check), cleanup, deletes, reaches, push plan
    steps = _close_steps(c)                                # [(name, fn)], built at call time
    if check_only: mark skipped; return _emit(c.report, 0)
    return _run_close_steps(c, steps)                      # lock span, inside-worktree exit 3, handoff after merge, push, cleanup
```

`_close_target` returns `_Close` with only the report filled in when it refuses: no change was named, or the name matched 0 or several worktrees. `_close_refusals` returns as soon as `trunk_refusal()` refuses, as today. `_emit` replaces the `emit` closure.

`_close_steps` builds its list on each call. Because no table is built at load, nothing evaluated at load reads `sdlc`, and a test's stand-in for a step's helper still reaches it.

`_run_close_steps` is the loop at lines 1037–1076, moved word for word. The lock stays in this one function, so one read shows the whole span it guards.

**Nit fixes:**

- R8: `_lead_line()` gains an optional `errors: list | None = None` parameter. Its `except Exception as e` appends to that list and still returns `(None, "lead=failed")`. The test's `lambda *_: (None, None)` stand-in still fits. `measure_change`'s `finish` passes `summary.setdefault("errors", [])`, and `_step_measure` copies a non-empty list into `report["measure"]["errors"]`. `metrics.trailers()` reads only named keys of the summary, so the trailers can't change.
- R9: `sdlc.py` line 3912 becomes `math.floor(round((cap - spent) * 100, 6)) / 100`. It still formats with `:g`.

**Edge cases.** A rerun that finds the change merged takes the lock before `remove folder`: that's the loop's first step, and `merge` is a no-op. A dropped change's list skips `merge` and `remove folder` and uses `record`. With the archive unavailable, the loop still `continue`s past `archive` without writing it to `done`, as today.

## Contracts touched

- **Closing: every git step refuses rather than forces, a rerun resumes, and the lock runs from the merge to the `Close` commit** (AGENTS.md *Closing*; REVIEW.md "Closing that can lose a change", "A destructive git flag in close"). The same git commands run in the same order under the same lock. Only where they live changes. R4, R6 and R11 check it.
- **`[review] sensitive` names `scripts/closing.py`.** All moved code stays in that file, so the full-depth review and the security reviewer apply. The change takes no new module, which would need a config edit to stay covered.
- **Modules loaded by path, bound live** (AGENTS.md; `tests/test_modules.py`). Steps call shared names as `sdlc.<name>` and close's own names as module globals. Nothing is evaluated at load. R3's names keep the line between script and module.
- **Metrics: trailers are a contract, and measuring never refuses** (`scripts/metrics.py`'s docstring). R8 leaves every trailer as it is and reports the failure only in close's JSON. ` lead=failed` keeps its documented meaning.
- **The register is committed only in the `Close` commit.** R10 retires the nits through `entries.md`, the way every change does.
- **Windows rules.** R12.
- **Nothing public names the agent.** No trailer is added.

No invariant needs to change.

## Alternatives rejected

- **Keep passing today's locals as parameters** (the open question). Each step would take 6–12 parameters. `report`, `kept` and `captured` would still be shared mutable state, only less visible. A dataclass makes that state explicit and gives the step signatures one shape. Rejected.
- **A class with step methods.** `closing.py` has no classes, and a test's stand-in would then be patched on an instance or a class, not on the module.
- **A step framework where each step declares its own "already done" check.** Each step resumes in its own way today: the merge is a no-op, the archive reuses its issue, the folder's removal is skipped. Turning that into a general mechanism changes how resuming works, and that is not a pure move.
- **A new module for the steps.** It would sit outside `[review] sensitive` until the config changed, which is the exact gap the sensitive list exists to close.
- **-3 by catching only expected exception types.** A programming error would then escape to `_step_measure`'s catch-all and cost every trailer, not just the lead line.
- **-3 as `lead=failed:<Type>` in `Sdlc-Coverage`.** It redefines a documented word in a trailer contract.
- **-3 as a line on stderr.** In this repo, close always runs in a handed-off child, and `_handoff()` drops a child's stderr when its report parses, so nobody would see the line.
- **-100 with `Decimal(str(spent))`.** Spending accumulates float noise (0.30000000000000004), so the result still loses a cent. Rounding at a millionth first removes the noise and still rounds down.
- **-2 by falling back to the tip's author date for `ready`.** In a factory change the tip is the landing commit, so it would report a `ready_wait` of about zero as if it had been measured. 162's D1 kept the code, and this change carries out that answer.

## Verification

```bash
uv run --group dev pytest -q -n auto tests/test_archive.py tests/test_cleanup.py tests/test_push.py \
  tests/test_register_lands.py tests/test_train.py tests/test_land.py tests/test_modules.py \
  tests/test_evals.py tests/test_windows.py tests/test_adoption.py
uv run --group dev pytest -q tests/test_archive.py::test_close_output_is_unchanged
uv run --group dev pytest -q -m portable
./check.sh
```

What healthy looks like:

- Every listed test passes. `test_close_output_is_unchanged` passes both at the change's first commit (old code) and at its tip.
- `git diff <first commit>..HEAD -- tests/` shows only the R3, R7, R8 and R9 additions.
- `./check.sh` ends green: ruff check, ruff format check, pytest and `claude plugin validate --strict`.
- At the close itself, this repo's close is handed to the merged code. Its report shows `"ran": "merged code"` and exit 0, and the `Close` commit carries the usual `Sdlc-*` trailers.

Boundaries:

- **Always:** a pure move plus the four nits.
- **Ask first:** R14's REFERENCE sentence. Also any change to a step's name, a report key or a trailer: the answer is no unless the person says otherwise.
- **Never:** change a git command, the lock span, the handoff protocol or the trailer format, or add a step.

