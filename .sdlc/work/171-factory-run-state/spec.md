---
id: 171
slug: factory-run-state
kind: spec
created: 2026-11-19
updated: 2026-11-19
---

# 171 — The factory's run state lives in a module of its own · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions, each checked in the code at this worktree's HEAD:

- `loop_state()` is the one reading of a build run. `cmd_verdicts()`, `cmd_agent()` and `cmd_upgrade()` all call it (`factory.py`, lines 2441, 4502 and 3510).
- `cmd_verdicts()` is a thin shell. It calls `loop_state()`, and with `--record` it writes `runs/stopped.md` (`stop_text()`) and `runs/step.md` (`_record_step()`, `step_text()`, `read_step()`). The board's copies of those records are pinned against `factory.stop_text`, `factory.step_text` and `factory.read_step` in `tests/test_board.py` (lines 385–1604).
- `landing.py` sets the pattern: loaded by path, bound to `_Names(globals())` as `factory`, and reading shared names as `factory.<name>`. `tests/test_modules.py` holds its line ("a function moves when it is named or only moved code calls it"). That file also holds `test_every_shared_name_is_the_factorys`, which compares `factory_records.py`'s constants against `factory.py`'s module globals.
- Most of the nits name code that 153 moved into `landing.py`, which `[review] sensitive` names. Two have already gone stale (see -68 below).

1. **R1. A module `plugins/factory/scripts/run_state.py` exists and holds the run's state reading.** It defines `loop_state`, `early_stop`, `settled`, `_untouched`, `cheap_nits`, `reworked`, `_gate_state` and `read_gate`, and `factory.py` defines none of them. `test_the_named_code_lives_in_its_module` and a by-name `test_the_run_state_lives_in_run_state` fail if `factory.py` still defines one, or if the module lacks one. The list is the named entry (`loop_state`) plus every function that only it calls today, by the rule in R3.
2. **R2. `factory.py` loads the module by path once and binds it live, as it does `landing.py`.** The binding is `run_state = _load_run_state()`, using `spec_from_file_location("factory_run_state", …/"run_state.py")` and `mod.factory = _Names(globals())`. The module has no `# /// script` block, no `__file__`, no `__name__`, and reads nothing as `factory.<name>` at load. `test_the_modules_are_loaded_by_path`, `test_the_modules_are_bound_live` and `test_the_modules_read_nothing_while_loading` each gain a `run_state` case and fail on any breach.
3. **R3. The line between script and module holds both ways.** `factory.py` reaches no function in `run_state.py` except `loop_state`. No function in `factory.py` is called only from `run_state.py`. `PAIRS` in `tests/test_modules.py` gains `(FACTORY_PY, RUN_STATE_PY, "run_state", "factory", RUN_STATE_NAMES, [LANDING_PY])`, and the landing pair's siblings become `[RUN_STATE_PY]`, so each module's `factory.<name>` calls count as the script's for the other. `test_the_line_between_script_and_module_holds` fails if a helper is left behind or moved too far.
4. **R4. The module defines no constant, regex or path.** Every one it reads (`GATE_FIXES`, `REVIEWERS`, `RUNS_THE_CHANGE`, `VERIFIED`, `NO_DECISION`, `UNTESTABLE_RE`, …) stays in `factory.py` and is read as `factory.<name>`. That keeps `test_every_shared_name_is_the_factorys` comparing `factory_records.py` against the same globals it compares today. A new `test_run_state_defines_no_constant` fails on any top-level `Assign` in the module other than `factory = None`.
5. **R5. It is a pure move.** Each moved function's body is the base's, except that a name it shares with `factory.py` is read as `factory.<name>`. `git diff --color-moved=zebra <base>...HEAD -- plugins/factory/scripts/` shows each body as moved, and the only changed lines inside it add that prefix. The reviewer checks this diff, and the plan names it as the code review's first check.
6. **R6. `verdicts`' JSON and every agent's prompt are unchanged on the existing fixtures.** Every test in `tests/test_factory.py`, `tests/test_prompts.py`, `tests/test_board.py`, `tests/test_land.py` and `tests/test_train.py` passes with its assertions untouched. In those files the diff only re-points call sites: `factory.loop_state` becomes `factory.run_state.loop_state`, and the same for `factory.read_gate`. The tests that build prompts from `loop_state()` (`_task()` is fed its `state`) fail on any changed byte. `tests/test_board.py` has no diff at all: the step and stop records stay in `factory.py`.
7. **R7. `cmd_verdicts()` and the run's records stay in `factory.py`.** `cmd_verdicts`, `cli_verdicts`, `stop_text`, `early_lines`, `step_text`, `read_step`, `_record_step` and `STOPPED` remain defined there. `test_the_run_state_lives_in_run_state` asserts it, so a later move can't silently cut the board's pins loose. `test_loop_state_reads_no_step_record` (test_factory.py:4366) reads `inspect.getsource(factory.run_state.loop_state)` and still finds no `STEP` or `read_step`.
8. **R8. Neither module ever loads `sdlc.py`.** `test_the_factory_never_loads_sdlc_py` is parametrised over `FACTORY_PY`, `LANDING_PY` and `RUN_STATE_PY`, and fails on an import naming `sdlc` or on `spec_from_file_location` naming it.
9. **R9. Nit 2026-11-18-80 is fixed.** In `landing.py`'s `cmd_land_fix`, `answered` is false when `reviews/land-<n>/` is missing, instead of `iterdir()` raising. `test_a_fix_asked_with_its_land_round_folder_gone_is_not_a_traceback` (test_land.py) removes the folder that `land_round()` counted, between its reading and the ask. Without the guard it raises `FileNotFoundError`. With the guard, the ask opens round `n` as an untouched one. In practice `land_round()` counts only existing folders, so this test drives `cmd_land_fix` with `land_round` stubbed on `factory`.
10. **R10. Nit 2026-11-18-69 is answered in the code.** A comment above `_run_loop()` says what a SIGKILL of the loop alone (not its process group) leaves behind. The agent subprocess it started lives on, because the run lock is held on the loop's own descriptor and children never inherit it, so a second `--run` can start while the orphan still writes. The one guard is that the same step named twice with nothing changed stops the loop, and the way out is to kill the group, as both kill tests do. No behaviour changes. Checkable by reading, and named in the plan's review checklist.
11. **R11. Nit 2026-11-18-84 is settled by a test.** `test_a_stack_conflicting_on_last_id_too_resolves` (test_train.py) builds a stack that conflicts on both `README.md` and `.sdlc/last-id`. The resolver writes only `README.md`, and `resolve --continue` goes through (`state: resolved`) with `.sdlc/last-id` holding the higher number. The test fails if `_stray()` counts the counter, which `_settle_counter()` stages before `_stray()` reads status. If `_conflicting()` already conflicts on the counter, the plan shows the existing test covers this and adds only the assertion on `last-id`.
12. **R12. Nit 2026-11-18-85 is fixed.** The `refused` helper in `test_a_resolution_outside_its_files_is_refused` takes a label (`"untracked"`, `"tracked"`), and every one of its assertion messages carries it, so a failure says which case broke.
13. **R13. Nit 2026-11-18-70 is fixed: each of the four R4 stops has a test of its own** in test_train.py. Each test fails if its stop is taken out:
    - a step whose command exits non-zero stops the loop, naming the exit;
    - an agent whose JSON holds `problem` stops it, naming the problem;
    - `resolve` with no conflicted files stops it, telling the person to run git status in the change's worktree;
    - a train reading `stop` for `land.moves` stops it with the train's own reason and `PUT_BACK`.

    The tests drive `factory.landing._run_plan` and `_run_loop`, with `factory.landing._run_one` and `_run_group` stubbed, so none needs `uv` or a fake `claude`.
14. **R14. Nit 2026-11-18-71 is fixed.** The kill test's wait is a `time.monotonic()` deadline of 60 s polled every 0.05 s, as `test_a_killed_check_frees_its_slot` does, in place of 600 × 0.2 s. It still ends the moment `<flag>.started` appears.
15. **R15. Nit 2026-11-18-98 is answered test by test.** Each of 155's five R3/R4 tests in test_factory.py either carries `@pytest.mark.portable` or a docstring sentence naming the POSIX-only piece it leans on (`start_new_session`/`killpg`, or a `sh` `sleep` whose kill CI's Windows job can't show). The tests are `test_two_checks_with_one_slot_run_one_after_the_other`, `test_a_check_waits_for_a_gates_slot`, `test_a_killed_check_frees_its_slot`, `test_a_check_past_the_timeout_is_killed` and `test_a_green_check_writes_nothing_and_never_clears_the_gate`. The plan decides each from what it runs. Checkable by reading.
16. **R16. Nit 2026-11-18-68 is answered, with no code change.** The `RUN_STEPS["eject"]` lookup it names is gone: `_run_plan()` reads `RUN_STEPS[nxt]` once, after the `RUN_EJECTS` check. `RUN_STOPS` is not unused: `test_every_reading_has_a_way_on` (test_train.py:1262) and line 1363 read it as the steps that are always the person's. The answer goes in the change's `notes.md`, and the nit is retired by naming it in this spec.
17. **R17. Idea 2026-11-18-67: a Windows kill test exists, marked `portable`.** `test_a_killed_train_run_resumes_on_windows` is skipped off Windows and marked `@needs_uv` and `@pytest.mark.portable`. It runs `train --run` with `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP`. It blocks at the gate, where the host's `[commands] check` writes a started flag and waits for good on its first call. It then kills the loop's tree with `taskkill /T /F /PID <pid>` and runs `train --run` again. That second run ends `done`, every change is closed once, and no `Close` commit carries another change's folder, as the POSIX test asserts. It blocks at the gate, not at an agent, because the fake `claude` is a shebang script that Windows can't start. The test fails on Windows if the killed run leaves state the next one can't resume. Off Windows it is skipped, never passed vacuously.
18. **R18. Nothing outside `plugins/factory/` and `tests/` changes.** `scripts/`, `defaults/`, `templates/`, `guide/`, `.sdlc/config.toml` and the skills have no diff. Ship's context check (`sdlc.py context`) decides whether `AGENTS.md`'s *Modules loaded by path* gains a clause, and if so it's that one clause. `git diff --stat <base>...HEAD` shows it.

## Design

**The module.** `plugins/factory/scripts/run_state.py` is shaped like `landing.py`:

- It opens with a docstring that states its contract. It holds the build loop's one reading (`loop_state()`) and the helpers only that reading calls. It writes nothing and runs no process except the `git` calls `factory._git` makes on its behalf. It never runs `claude` and never runs a host's command.
- Then `from __future__ import annotations`, the stdlib imports its bodies use (`Path`, `re` where needed), and `factory = None`.
- Then the eight functions, in their order in `factory.py` today.
- The docstring also says where the line falls, so the next reader doesn't re-derive it. A function lives here when it is `loop_state` or only code here calls it. Constants and record formats stay in `factory.py`, where `factory_records.py`'s pins compare them. So do `cmd_verdicts` and the records it writes, which the board's copies follow.

**Loading.** `factory.py` gains `_load_run_state()` beside `_load_landing()`, a copy of it with the module's name and file. It is assigned as `run_state = _load_run_state()` right after `landing = _load_landing()`, at the bottom, after every global exists. `_Names` is shared. `run_state` holds `loop_state`, which is called at runtime only, never at load, so the late binding is safe, as it is for `landing`.

**Call sites.** In `factory.py`, `cmd_verdicts`, `cmd_agent` and `cmd_upgrade` call `run_state.loop_state(...)`. No other code in `factory.py` names a moved function. Inside the moved bodies, each name `factory.py` keeps becomes `factory.<name>`, for example:

- `load_config`, `find_change`, `_rounds_at_depth`, `read_decision`
- `_git`, `frontmatter`, `change_tier`, `read_ledger`, `build_round`
- `GATE_FIXES`, `read_evidence`, `RUNS_THE_CHANGE`, `REVIEWERS`, `preamble`, `_no_verdict`
- `VERIFIED`, `read_verified`, `decision_preamble`, `NO_DECISION`, `mended`, `upgrade_answer`, `_scaffold`
- `_base`, `_base_check`, `read_gate_file`, `gate_path`, `build_hash`, `read_snapshot`, `_change_path`, `UNTESTABLE_RE`

Calls between moved functions stay bare: `early_stop`, `settled`, `_untouched`, `cheap_nits`, `reworked`, `_gate_state`, `read_gate`. Reading through `factory.` keeps a test's `monkeypatch.setattr(factory, "_git", …)` reaching the moved code, as it does for `landing.py`.

**Why this boundary** (the intent's open question). The module holds the state and the decision, not `cmd_agent`'s task building:

- `_task()`, `_task_prompt()` and `_land_task()` are prompt assembly. They read `prompts/` (`prompt_part()`), `FACTORY_SCRIPT` (`check_line()`) and the screenshots, and `_land_task` is the landing's.
- Moving them is a second seam with a different reason to change: prompt wording, not loop logic. It would also split `cmd_agent` from the prompt it sends.
- `cmd_agent` stays in `factory.py` either way, as the one place `claude` runs.
- So this change takes `loop_state`'s share of the churn (the hottest decision logic) and leaves `cmd_agent`'s for a later change, if R3's index still ranks it.

**`cmd_verdicts` stays.** Its body is `loop_state()` plus writing two records whose formats the board copies. If it moved, `stop_text`, `step_text`, `read_step` and `_record_step` would have to follow it by R3's rule, and `tests/test_board.py`'s pins on `factory.stop_text` and `factory.read_step` would follow them. That falls outside what the intent named. The step list in its docstring stays where `verdicts`' readers look for it.

**The nits.**

- -80 is one guard in `landing.py`: `answered = n and (d := folder / "reviews" / f"land-{n}").is_dir() and any(d.iterdir())`.
- -69 is a comment in `landing.py`.
- -84, -85, -70 and -71 are tests.
- -98 is marks or docstring sentences.
- -68 is answered in `notes.md`.
- The Windows kill test reuses `_three()`, `_begin()` and `_loop()` from `tests/test_train.py`. Its check is a `sys.executable -c` one-liner, quoted for `_sh()`, that writes `<flag>.started` and loops when `<flag>` is absent, and exits 0 once `<flag>` exists.

**Edge cases.**

- A test that stubs `factory.loop_state` would no longer reach `cmd_agent`. None does (checked: no `monkeypatch.setattr(factory, "loop_state", …)` anywhere in `tests/`).
- `factory.run_state` exists only once `factory.py` has finished loading. Tests always load the whole script, so this holds.

## Contracts touched

- **`factory.py agent` is the one place the factory runs `claude`** (AGENTS.md, *The factory*). `cmd_agent` and `_claude()` stay in `factory.py`. `run_state.py` runs no process except `factory._git`. R1 and R5 hold it.
- **`verdicts` decides from the rounds alone and reads no state file but `runs/mended`.** The moved code is unchanged (R5), still reads `mended()` through `factory.`, and still never reads `runs/step.md` (R7's source check).
- **The factory never imports `sdlc.py`** (AGENTS.md; `test_the_factory_never_loads_sdlc_py`). Extended to the new module (R8).
- **Modules loaded by path, never imported, and bound live** (AGENTS.md, *Modules loaded by path*). The design follows `landing.py` exactly (R2), and `test_modules.py`'s rules gain a case each (R2, R3).
- **Core's copies of a run's records live in `factory_records.py` under `factory.py`'s names, pinned** (`test_every_shared_name_is_the_factorys`). Constants stay in `factory.py` (R4), and the record writers stay with `cmd_verdicts` (R7), so every pin compares the same thing it does today.
- **`[review] sensitive` is read from the base branch.** `landing.py` is listed, and R9 and R10 edit it. That puts the whole change under full-depth review with the security reviewer, and the factory's gate can't pass itself (`Sdlc-Landed: by=auto` is off the table). That's intended, not a side effect: see the second open question. `run_state.py` is not added to `[review] sensitive`, since that's a config edit outside the factory and the module is not on the commit path.
- **The scripts run on Windows** (`tests/test_windows.py`). The module imports nothing platform-specific and writes no file. The new Windows test imports nothing at the top that exists on only one platform: `CREATE_NEW_PROCESS_GROUP` is read only inside the test body, behind its skip.
- **Every text-mode `subprocess.run` names `encoding="utf-8"`.** The new tests' `taskkill` and `Popen` calls do.

No invariant needs to change.

## Alternatives rejected

- **Move `cmd_agent`'s task building (`_task`, `_task_prompt`) too.** It's a different seam (prompt wording), it needs `prompts/` and `FACTORY_SCRIPT`, and it would double the diff of a change whose point is a safe move. Left for its own change if `cmd_agent` stays hot after this.
- **Move `cmd_verdicts` and its record writers.** That cuts `tests/test_board.py`'s pins (`factory.stop_text`, `factory.read_step`) loose, against "nothing outside the factory changes". It also puts record formats that `factory_records.py` copies into a second file. `landing.py` set the precedent: its records (`_record_land`, `read_land_step`) stayed in `factory.py`.
- **Move the constants the moved code reads.** `test_every_shared_name_is_the_factorys` compares `factory_records.py` against `factory.py`'s globals only, so a moved `NO_DECISION` or `VERIFIED` would silently drop out of the pin.
- **Leave aliases (`loop_state = run_state.loop_state`) in `factory.py`.** That spares the tests a rename, but R3's test reads each alias as the script reaching an unnamed name. It also leaves two names for one function, which the next change edits by the wrong one.
- **Import the module normally, or add to `sys.path`.** `uv run --script` and the tests resolve imports differently (AGENTS.md), and `test_the_modules_are_loaded_by_path` refuses both.
- **Fix -69 by making the run lock inheritable to the children.** That changes behaviour in `landing.py` mid-move. It also doesn't carry over to `msvcrt` locking, which is per handle. The nit asked for a comment or a test.
- **A Windows kill test that blocks in a fake agent.** The fake `claude` is a shebang file Windows can't start, and a `.cmd` shim isn't found by `CreateProcess` for a bare `claude` argv. Blocking in the gate uses only `_sh()` and `sys.executable`.
- **Delete `RUN_STOPS` (-68).** Two tests read it as the person's steps.

## Verification

```bash
./check.sh
# healthy: ruff check and ruff format --check clean; pytest -n auto all passed (the new tests
# included, the Windows kill test reported skipped off Windows); claude plugin validate --strict ok

uv run --group dev pytest -q tests/test_modules.py
# healthy: every parametrised case passes, the run_state cases included (R1–R4, R8)

uv run --group dev pytest -q -n auto tests/test_factory.py tests/test_prompts.py tests/test_board.py tests/test_land.py tests/test_train.py
# healthy: all passed (R6, R7, R9, R11–R14)

git diff --color-moved=zebra "$(git merge-base HEAD main)"...HEAD -- plugins/factory/scripts/
# healthy: the moved functions show as moved blocks; inside them only lines adding `factory.`
# differ (R5); landing.py shows the -80 guard and the -69 comment alone (R9, R10)

git diff --stat "$(git merge-base HEAD main)"...HEAD -- tests/test_board.py scripts/ defaults/ templates/ guide/ skills/ .sdlc/config.toml
# healthy: empty (R6, R18)

git diff "$(git merge-base HEAD main)"...HEAD -- tests/test_factory.py tests/test_prompts.py tests/test_land.py | grep '^[-+] .*assert'
# healthy: only lines where `factory.loop_state` / `factory.read_gate` became
# `factory.run_state.…`, plus R15's marks; no assertion's expected value changed (R6)

uv run --group dev pytest -q -m portable
# healthy: passes here; on CI's Windows job `test_a_killed_train_run_resumes_on_windows` runs
# and passes (R17)
```

(Here `main` stands for the base branch `sdlc.py config` names in `git.base`.)

