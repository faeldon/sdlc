A factory change at `stage: plan` now shows under Designing while its spec-writer runs or its draft waits for the person's yes. That holds on the board and in `/sdlc:status`, and its `stage:` line is never changed. The new tests pass by name and ruff is clean. The full gate hasn't run yet; the factory runs it next.

**One point where the code differs from the intent.** The intent says a running spec-writer shows in `runs/step.md`. That's only true for an upgraded Tier 1: a Tier 2's first draft writes no step record. So a spec-writer counts as still running when the newest session id in `runs/spec-writer.sessions` has no row yet in `runs/costs.jsonl`. That row is written when the session returns. This keeps the intent's other rule: after a no, once the draft is deleted, the change goes back to Planned.

**What was built (one slice):**
- **`scripts/factory_records.py`:** a new `specifying(folder)` says whether a spec is under way. It is true when `runs/spec-draft.md` exists, when `runs/step.md` names `spec`, or when the newest spec-writer session hasn't returned. `reading()` (used by `status`) and `card_reading()` (used by the board) both include it. Two new path constants: `SPEC_DRAFT`, under the same name as `factory.py`'s so the existing test pins it, and `SPEC_SESSIONS`.
- **`scripts/sdlc.py`:** `column()` puts a factory change at `plan` with `specifying` under Designing. A spec already written at `plan` still goes to Needs you first, as before.
- **`docs/REFERENCE.md`:** the board's description of Designing now mentions this case.

**Tests added:**
- `tests/test_board.py::test_a_plan_change_being_specified_is_designing` checks five plan-stage factory changes on both the board and `status`. Three are Designing: an upgraded run's step record, a waiting draft, and a session that hasn't returned. Two stay Planned: a returned session whose draft is gone, and one with neither. It also checks that no `stage:` line changed. It failed before the code change and passes now.
- `tests/test_modules.py::test_spec_sessions_is_the_spec_writers_file` ties `SPEC_SESSIONS` to the file name `factory.py agent` uses for the spec-writer. `specifying`, `SPEC_SESSIONS` and `SPEC_DRAFT` were added to `RECORD_NAMES`.

**`plan.md`:** written before the code, since this Tier 1 change touches more than a couple of files. Afterwards I added the second test and the REFERENCE.md edit to it.

**`notes.md`:** one open item. The board's step track shows nothing for a first spec draft; a Designing card could show a `spec` step with its elapsed time.

- DECISION: [default] Keep a draft waiting for the yes under Designing, not Needs you (the intent's open question). Going ahead with Designing unless told otherwise.
  - OPTION: Designing — matches the intent's Outcome and the person's words; the waiting yes shows only as the change sitting there
  - OPTION: Needs you for a waiting draft, Designing only while the spec-writer runs — puts the owed yes in front of the person; differs from the Outcome as written
  - WHY: the intent's Outcome and its test line both say a waiting draft lands in Designing
- DECISION: [default] Count a spec-writer as running when its newest session has no row in `runs/costs.jsonl`, since a first draft writes no `runs/step.md`. Going ahead with this unless told otherwise.
  - OPTION: a session with no cost row — catches the first draft; a session that dies without reporting costs stays under Designing until its folder is cleared
  - OPTION: only `runs/step.md` and `runs/spec-draft.md`, as the Approach says — simpler; a first draft shows Planned while it runs, which misses the Outcome
  - OPTION: have `factory.py agent --task spec` write a step record — one signal for both cases; changes the factory and `runs/step.md`'s meaning, outside the change's Affected list
  - WHY: the Outcome asks for Designing "while its spec-writer runs", and this is the only record a first draft leaves without touching the factory

## Evidence

$ uv run --group dev pytest tests/test_board.py::test_a_plan_change_being_specified_is_designing -q
E             At index 1 diff: 'planned' != 'designing'
FAILED tests/test_board.py::test_a_plan_change_being_specified_is_designing
1 failed in 7.61s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py::test_a_plan_change_being_specified_is_designing tests/test_modules.py::test_spec_sessions_is_the_spec_writers_file tests/test_modules.py::test_every_shared_name_is_the_factorys tests/test_modules.py::test_the_record_readers_live_in_factory_records tests/test_modules.py::test_no_factory_record_is_named_outside_its_reader
.....                                                                    [100%]
5 passed in 3.82s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_modules.py tests/test_board.py tests/test_feature_map.py
332 passed, 28 skipped in 13.23s
exit: 0

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
312 files already formatted
exit: 0
