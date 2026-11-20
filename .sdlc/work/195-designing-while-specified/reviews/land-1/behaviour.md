VERDICT: PASS

I found no failures. A factory change at `stage: plan` whose spec is under way now shows under Designing. The spec-writer reaching the board and `/sdlc:status` depends on the signals below, and the change's own tests cover them.

## Notes
- **End-to-end path:** the intent names no command, so I ran the tests the change added for the board and the module pin. All 3 passed (`test_a_plan_change_being_specified_is_designing`, `test_spec_sessions_is_the_spec_writers_file`, and one other that matched the filter).
- **What the code does:**
  - `specifying()` returns true when `runs/spec-draft.md` exists, when `runs/step.md` names `spec`, or when the newest `runs/spec-writer.sessions` id has no `runs/costs.jsonl` row.
  - `column()` maps `plan` + factory + `specifying` to `designing`.
  - It does not change `stage:`.
  - `column()` stays the one shared rule.
  - `SPEC_SESSIONS` and `SPEC_DRAFT` are pinned to `factory.py`'s naming in `tests/test_modules.py`.
- **Difference from the intent's Approach:** the Approach says a draft waits when `spec-draft.md` exists and `spec.md` is still its scaffold. The code treats any `spec-draft.md` as waiting. I'm not raising it as a CHANGE: once the draft is accepted and the stage moves on, the column no longer reads `plan`, and the draft being gone returns the change to Planned. The spec-writer-running signal is covered by decision D2, which is settled.
- **Decisions:** D1 and D2 are answered, so I did not raise them again. The known cost is that a spec-writer session that dies leaves its card under Designing.
- **The gate:** `build/round-1.gate.md` ends in `✔ Validation passed`. I did not rerun it.
- **checks.md:** none exists for this change.

## Evidence
$ git diff df3cca4b35a5d55cf5d895ffdf365ccf98b0661d...HEAD --stat | tail -3
 tests/test_modules.py                              | 14 +++-
 26 files changed, 541 insertions(+), 11 deletions(-)
exit: 0

$ uv run --group dev pytest -q tests/test_board.py tests/test_modules.py -k "specified or specifying or spec_sessions or designing"
3 passed, 349 deselected in 2.95s
exit: 0

$ tail -3 .sdlc/work/195-designing-while-specified/build/round-1.gate.md
    ✔ Validation passed
exit: 0

$ ls .sdlc/work/195-designing-while-specified/checks.md
ls: .sdlc/work/195-designing-while-specified/checks.md: No such file or directory
exit: 1
