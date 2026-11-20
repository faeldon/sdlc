VERDICT: PASS

The new column rule does what the intent's Outcome asks. A factory change at `stage: plan` shows under Designing while its spec-writer runs or its draft waits for the yes, and the same rule feeds both the board and `status`. I ran the two new tests and both pass.

## Notes
- **No `spec.md` or `checks.md` in this change.** It is Tier 1, so there is no `checks.md` to read and nothing to run from one. I took the intent's Approach as the end-to-end path. The closest runnable path is the new test, `test_a_plan_change_being_specified_is_designing`. It builds five `plan` changes, then reads their columns from the board's cards and from `status`:
  - Designing in both: an upgraded run whose `step.md` names `spec`, a waiting draft, and a spec-writer session with no cost row yet.
  - Planned in both: a returned session whose draft is gone, and a change with neither signal.
  - All five keep `stage: plan` in `intent.md`.
- **The waiting-draft check differs from the Approach in one way.** The Approach says the draft counts only while `spec.md` is still its scaffold. `specifying()` checks only that `runs/spec-draft.md` exists. After the yes the change moves to `design`, and `column()` applies the rule only at `plan`, so I found no effect from it.
- **D1 and D2 in `decisions.md` are the builder's defaults and still open.** D1 keeps a waiting draft under Designing rather than Needs you. D2 counts a spec-writer as running when its newest session has no row in `runs/costs.jsonl`. I did not raise them again, since the builder already raised them and the person answers them at ship.
- **The gate is green for this round.** I read `build/round-1.gate.md`, which says `GATE: PASS`, and did not run the suite or the gate.

## Evidence
$ uv run --group dev pytest -q tests/test_board.py::test_a_plan_change_being_specified_is_designing tests/test_modules.py::test_spec_sessions_is_the_spec_writers_file
..                                                                       [100%]
2 passed in 10.89s
exit: 0

$ head -5 .sdlc/work/195-designing-while-specified/build/round-1.gate.md
GATE: PASS

## Attempt 1

Verdict: PASS
exit: 0

$ git diff $(git merge-base HEAD main) -- scripts docs tests
(diff read: `specifying()` in `factory_records.py`, the `plan` and `specifying` branch in `column()`, the new tests, the REFERENCE.md line)
exit: 0

$ grep -n "spec-draft\|spec-writer.sessions\|\.sessions" plugins/factory/scripts/factory.py | head
51:`agent` the reply an agent session returned (a spec draft to `runs/spec-draft.md` and its
3277:    """Copy `runs/spec-draft.md` into `spec.md`, byte for byte, once the person said yes. Refused,
3689:SPEC_DRAFT = Path("runs") / "spec-draft.md"
exit: 0
