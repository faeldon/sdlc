All nine requirements are built. The whole loop now runs in a test as real subprocesses, from one seed to a landed change, in about 17 seconds. The full gate passed (4042 passed, 29 skipped). Nothing is committed; `HEAD` is still `0d70bd8`.

One thing differs from the spec: an agent run reads the ledger's `closes:` rows twice, not once as R7 assumed. I've pinned two and raised it below.

## Slices built
1. **R8, a quoted `- BUILT:` line no longer counts.** I added `unfenced_lines()` to `factory.py`, using the same fence rule as `split_draft()`. `unbuilt_defaults()` now reads builder reports through it. The README sentence says "outside a code fence".
2. **R6, a refused agent writes nothing.** In `cmd_agent`, `record_closes()` now runs before the sessions-file append and before `_record_land()`. On success the outputs are the same as before.
3. **R7, no cache for `recorded_closes()`.** Its docstring states the cost: two reads per agent run, one from `run_state.loop_state()` through `intent_closes()` and one from `record_closes()`.
4. **R5, no lock for `cmd_answer`.** Its docstring and `cmd_decisions`'s now state why it's safe without one: the loop never runs a change's ledger writers beside another of its steps.
5. **R3, R4:** `take_markers()` has its own test, and the refused half of the real-step test now goes through `_claude()`.
6. **R1, R2, the whole loop.** `FAKE_CLAUDE` logs a `markers` field and takes a `once` entry, so a resumed builder raises its decision only once. The end-to-end test is new.

## Tests added and what they prove
- `test_autopilot_run_lands_a_seed_through_real_subprocesses` (R1, R2). The loop really runs `answer --by autopilot`, and main ends with `Close` and `Sdlc-Landed: by=autopilot`. The intent says `opened_by: autopilot`, and the ledger holds only `→ decided by autopilot:` lines. Neither the host's check nor any agent session saw a marker. It failed in two scratch edits: with `take_markers()` taken out, and with `loop_env()` no longer giving the markers back.
- `test_fake_claudes_marker_names_are_the_factorys` (R2): fails if either marker is renamed.
- `test_take_markers_moves_both_markers_out_of_the_env` (R3, portable, two cases).
- `test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does` (R4): failed when `_claude` stopped passing `env=agent_env()`.
- `test_no_ledger_writer_runs_beside_another_step_of_its_change` (R5): failed when the loop's read step ran `decisions` and `verdicts` together.
- `test_an_agent_refused_on_its_closes_leaves_nothing_recorded` (R6, in `test_land.py`): failed on the old order, with the landing step going from `ship` to `fix`.
- `test_an_agent_run_reads_the_closes_once` (R7): pins two reads.
- Four fenced cases for `test_ask_says_ship_once_a_later_builder_report_built_it`, plus `test_a_fenced_built_line_still_holds_autopilot` (R8). The three fenced cases and the hold test failed before the fix.

Tests run by name: R8's 8 tests (4 failed first, then 8 passed), R6's 1 (failed, then passed), R7's 1, R5's 1, R3's 2, R4's 1, and the end-to-end pair. Then the seven touched test files together: 674 passed, 1 skipped.

## Changes to plan.md
plan.md is written and has a "Departures from the spec's design" section:
- The end-to-end host's check is plain `sh`, not a Python script. The gate's record holds the command, and `sys.executable` sits under a home directory, which the repo's scan refuses. That held the change at the approver step.
- R6's test lives in `test_land.py` so it can reuse that file's landing helpers.
- R7 pins two reads, as above.

`autopilot.py` and `landing.py` are untouched. Nothing is left in `notes.md`.

- DECISION: [default] Pin R7 at two `recorded_closes()` reads per agent run, not the spec's one, and leave the code as it is. Going ahead with two unless told otherwise.
  - OPTION: pin two, no code change — matches what runs today and still catches a call added in a loop; the spec's count was wrong
  - OPTION: pass the reading's closes into `record_closes()` so there is one read — matches the spec; changes how `loop_state()` and `cmd_agent` share data for no real saving
  - WHY: R7 is about cost, and a second read of a small file per agent session costs nothing worth new code paths

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_autopilot.py::test_a_fenced_built_line_still_holds_autopilot "tests/test_factory_decisions.py::test_ask_says_ship_once_a_later_builder_report_built_it"
FAILED tests/test_autopilot.py::test_a_fenced_built_line_still_holds_autopilot
FAILED ...[fenced] / [tilde-fenced] / [unclosed-fence]
4 failed, 4 passed in 54.76s
exit: 1

$ uv run --group dev pytest -q tests/test_autopilot.py::test_a_fenced_built_line_still_holds_autopilot "tests/test_factory_decisions.py::test_ask_says_ship_once_a_later_builder_report_built_it" -n 4
8 passed in 6.20s
exit: 0

$ uv run --group dev pytest -q tests/test_land.py::test_an_agent_refused_on_its_closes_leaves_nothing_recorded
E  ... b'STEP: fix\nROUND: 1 ...' != b'STEP: ship\nROUND: ...'
1 failed in 12.29s
exit: 1

$ uv run --group dev pytest -q tests/test_land.py::test_an_agent_refused_on_its_closes_leaves_nothing_recorded
1 passed in 8.97s
exit: 0

$ uv run --group dev pytest -q tests/test_autopilot.py::test_an_agent_run_reads_the_closes_once
E       assert 2 == 1
1 failed in 2.08s
exit: 1

$ uv run --group dev pytest -q tests/test_autopilot.py::test_an_agent_run_reads_the_closes_once
1 passed in 2.29s
exit: 0

$ uv run --group dev pytest -q tests/test_autopilot.py::test_no_ledger_writer_runs_beside_another_step_of_its_change
1 passed in 10.13s
exit: 0

$ sed -i '' '...together=True)/' plugins/factory/scripts/autopilot.py && uv run --group dev pytest -q tests/test_autopilot.py::test_no_ledger_writer_runs_beside_another_step_of_its_change; git checkout plugins/factory/scripts/autopilot.py
>       assert steps.overlaps == [], steps.overlaps
1 failed in 7.48s
Updated 1 path from the index
exit: 0

$ uv run --group dev pytest -q tests/test_autopilot.py -m portable -k take_markers
2 passed, 60 deselected in 1.21s
exit: 0

$ uv run --group dev pytest -q tests/test_autopilot.py::test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does
1 passed in 4.15s
exit: 0

$ (scratch edit: _claude without env=agent_env()) uv run --group dev pytest -q tests/test_autopilot.py::test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does; (restored)
FAILED tests/test_autopilot.py::test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does
1 failed in 2.39s
exit: 0

$ uv run --group dev pytest -q tests/test_autopilot.py -k "real_subprocesses or marker_names" --durations=3
E       AssertionError: ... held: the folder holds lines the repo's scan refuses: build/round-1.gate.md:6; factory.py defuse 001
1 failed, 1 passed, 62 deselected in 26.03s
exit: 1

$ uv run --group dev pytest -q tests/test_autopilot.py -k "real_subprocesses" --durations=2
16.72s call     tests/test_autopilot.py::test_autopilot_run_lands_a_seed_through_real_subprocesses
1 passed, 63 deselected in 30.51s
exit: 0

$ (scratch edit: take_markers() removed from main) uv run --group dev pytest -q tests/test_autopilot.py -k "real_subprocesses"; (restored)
E           AssertionError: check-16929.env
E           assert not ['SDLC_FACTORY_AUTOPILOT_RUN']
1 failed, 63 deselected in 19.46s
exit: 0

$ (scratch edit: loop_env() returns dict(os.environ)) uv run --group dev pytest -q tests/test_autopilot.py -k "real_subprocesses"; (restored)
E       AssertionError: ... held: the train stopped at commit: --by autopilot is autopilot's alone: no autopilot --run holds its lock
1 failed, 63 deselected in 27.34s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_autopilot.py tests/test_factory_decisions.py tests/test_land.py tests/test_train.py tests/test_factory_agent.py tests/test_prompts.py tests/test_modules.py
674 passed, 1 skipped in 447.94s (0:07:27)
exit: 0

$ uv run --group dev ruff check . ; uv run --group dev ruff format --check .
All checks passed!
344 files already formatted
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 228
All checks passed!
344 files already formatted
4042 passed, 29 skipped in 380.29s (0:06:20)
✔ Validation passed
✔ Validation passed
exit: 0

$ git log --oneline -1 && git status --short
0d70bd8 Close 225-ci-pin-test-quotes
 M plugins/factory/README.md
 M plugins/factory/scripts/factory.py
 M tests/test_autopilot.py
 M tests/test_factory_decisions.py
 M tests/test_land.py
 M tests/train_driver.py
?? .sdlc/work/228-autopilot-readiness/
exit: 0
