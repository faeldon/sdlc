All of change 171 is built and left uncommitted. The full gate passed: 3078 tests passed in the first full run, and the rerun after the last fix exited 0. Two places went beyond the spec: I moved one more function than it listed, and I re-pointed one more test file than R6 named.

**The move (R1–R8):** I did the move with a one-off script. It copied each function verbatim and added the `factory.` prefix only to names `factory.py` keeps. The new `plugins/factory/scripts/run_state.py` now holds `loop_state` and its helpers.
- **One function the spec missed:** `decision_preamble` is called only by `loop_state`, so R3's rule (which R1 says decides the list) moves it too. The new R3 test failed until it moved. That makes nine functions, not eight.
- **Pure move (R5):** I compared each of the nine against the base after removing the prefix, and all nine have identical syntax trees.
- **Loading:** `factory.py` gains `_load_run_state()` and `run_state = _load_run_state()`. `cmd_verdicts`, `cmd_upgrade` and `cmd_agent` now call `run_state.loop_state`. Constants, `cmd_verdicts` and the records it writes stay in `factory.py`.
- **Test re-points:** in `tests/test_factory.py`, 17 call sites change from `factory.loop_state`/`factory.read_gate` to `factory.run_state.…`, with no assertion changed. `tests/test_board.py` and `tests/test_prompts.py` have no diff.
- **Outside R6's list:** `tests/test_skills.py::test_the_build_skill_handles_every_step_verdicts_names` reads `loop_state`'s source text from `factory.py`, which made the first gate run red. I pointed it at `run_state.py`.
- **`tests/test_modules.py`:** gains a `run_state` case in every rule, plus `test_the_run_state_lives_in_run_state` (R1, and R7's names staying in `factory.py`) and `test_run_state_defines_no_constant` (R4).

**The nits:**
- **R9 (-80):** `test_a_fix_asked_with_its_land_round_folder_gone_is_not_a_traceback` failed first with `FileNotFoundError`. A one-line guard in `cmd_land_fix` fixes it.
- **R10 (-69):** a comment above `_run_loop()`, to check by reading.
- **R11 (-84):** `test_a_stack_conflicting_on_last_id_too_resolves` first checks that both sides of the paused rebase hold different `.sdlc/last-id` values, then that the counter is settled and `--continue` resolves it to `002`. When I made `_stray` count the counter, it failed ("edited outside its conflicted files: .sdlc/last-id").
- **R12 (-85):** `refused(label, stray)`, with the label in every assertion message.
- **R13 (-70):** four tests drive `_run_loop` with `_run_one` and `_run_group` stubbed, so they start no process and are marked `portable`: `test_train_run_stops_at_a_failed_step`, `…_at_an_agents_problem`, `…_at_a_resolve_with_no_conflict` and `…_at_the_trains_stop`. Each failed on an assertion when I took its stop out of `landing.py`.
- **R14 (-71):** a 60 s `time.monotonic()` deadline, polled every 0.05 s.
- **R15 (-98):**
  - Marked `portable`: `test_two_checks_with_one_slot_run_one_after_the_other`, `test_a_check_waits_for_a_gates_slot` and `test_a_green_check_writes_nothing_and_never_clears_the_gate`.
  - Given a docstring sentence instead: `test_a_killed_check_frees_its_slot` (`start_new_session`/`killpg`) and `test_a_check_past_the_timeout_is_killed` (it kills an `sh` that `exec`s `sleep`).
- **R16 (-68):** answered in `notes.md`, with no code change.

**R17 (idea -67):** `test_a_killed_train_run_resumes_on_windows` is skipped here. It kills the loop's process tree with `taskkill /T /F` while the host's check blocks at the gate. Before rerunning, it writes the behaviour replies the stacked changes need, so no agent has to start (the fake `claude` can't run on Windows). The test body is a helper that a second test, `test_a_train_run_killed_at_its_gate_resumes`, also runs here with `killpg`, and that one passes. The Windows test itself only runs on CI's Windows job.

**R18:** nothing outside `plugins/factory/`, `tests/` and the change folder changed. I left `AGENTS.md` for ship's context check, as the spec says.

**plan.md:** written before the code. It was then updated for the ninth function, the POSIX twin test, and the `test_skills.py` re-point.

**notes.md:** holds -68's answer, the `decision_preamble` move, the twin test, and the `test_skills.py` re-point. Nothing is left unticked.

- DECISION: [default] Move `decision_preamble` into `run_state.py` too, beyond R1's list of eight? Going ahead with moving it unless told otherwise.
  - OPTION: move it — R3's rule holds both ways and R1 says that rule decides the list; the module has nine functions, not eight
  - OPTION: keep it in `factory.py` — matches R1's list word for word; needs an exception in R3's test, which then no longer holds both ways
  - WHY: R1 says its list is "the named entry plus every function that only it calls today, by the rule in R3", and only `loop_state` calls `decision_preamble`.

## Evidence

$ uv run --group dev pytest -q tests/test_modules.py
25 passed in 10.86s
exit: 0

$ uv run --group dev pytest -q tests/test_land.py::test_a_fix_asked_with_its_land_round_folder_gone_is_not_a_traceback   (before the guard)
E       FileNotFoundError: [Errno 2] No such file or directory: '…/.sdlc/work/001-gone/reviews/land-1'
1 failed in 2.66s
exit: 1

$ uv run --group dev pytest -q tests/test_land.py::test_a_fix_asked_with_its_land_round_folder_gone_is_not_a_traceback   (after)
1 passed in 1.44s
exit: 0

$ uv run --group dev pytest -q tests/test_train.py::test_a_stack_conflicting_on_last_id_too_resolves
1 passed in 15.33s
exit: 0

$ uv run --group dev pytest -q tests/test_train.py::test_a_stack_conflicting_on_last_id_too_resolves   (with `_stray` counting the counter, reverted after)
E       AssertionError: {'state': 'refused', 'refusals': ['edited outside its conflicted files: .sdlc/last-id']}
exit: 1

$ uv run --group dev pytest -q tests/test_train.py::test_a_resolution_outside_its_files_is_refused
1 passed in 16.33s
exit: 0

$ uv run --group dev pytest -q tests/test_train.py -k "stops_at_a_failed_step or stops_at_an_agents_problem or resolve_with_no_conflict or stops_at_the_trains_stop"
4 passed, 48 deselected in 0.55s
exit: 0

$ (each of the four stops taken out of landing.py in turn, then restored) uv run --group dev pytest -q tests/test_train.py -k <its test>
== stops_at_a_failed_step: 1 failed, 51 deselected in 0.16s
== stops_at_an_agents_problem: 1 failed, 51 deselected in 0.14s
== resolve_with_no_conflict: 1 failed, 51 deselected in 0.13s
== stops_at_the_trains_stop: 1 failed, 51 deselected in 0.10s
exit: 1

$ uv run --group dev pytest -q tests/test_train.py -k "killed" -rs
SKIPPED [1] tests/test_train.py:1846: kills a process tree with taskkill, on Windows
2 passed, 1 skipped, 51 deselected in 117.06s (0:01:57)
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py -k "two_checks_with_one_slot or check_waits_for_a_gates_slot or killed_check_frees or check_past_the_timeout or green_check_writes_nothing"
5 passed, 355 deselected in 6.45s
exit: 0

$ python3 (AST comparison of each run_state.py function against HEAD's factory.py, `factory.` removed)
reworked identical | _untouched identical | settled identical | decision_preamble identical | loop_state identical | early_stop identical | cheap_nits identical | read_gate identical | _gate_state identical
exit: 0

$ git diff --stat HEAD -- scripts defaults templates guide skills .sdlc/config.toml tests/test_board.py tests/test_prompts.py
(no output)
exit: 0

$ uv run --quiet --script …/plugins/factory/scripts/factory.py check 171   (first run)
FAILED tests/test_skills.py::test_the_build_skill_handles_every_step_verdicts_names
1 failed, 3078 passed, 29 skipped in 139.07s (0:02:19)
exit: 1

$ uv run --group dev pytest -q tests/test_skills.py::test_the_build_skill_handles_every_step_verdicts_names
1 passed in 0.22s
exit: 0

$ uv run --quiet --script …/plugins/factory/scripts/factory.py check 171   (after the re-point)
✔ Validation passed
exit: 0
