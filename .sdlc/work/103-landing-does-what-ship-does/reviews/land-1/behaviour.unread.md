VERDICT: PASS

## Notes
- `checks.md`: this change has none, so there is nothing to read.
- The spec's end-to-end path is R13: a batch of three changes lands through `factory.py` alone. The three changes are one with `checks.md`, one with an undone note and one touching an irreversible path. `test_a_batch_with_checks_a_note_and_an_irreversible_path_lands_through_factory_alone` passes. So do the carry/drop/confirm and recovery tests.
- The related suites (`test_land.py`, `test_skills.py`, `test_factory.py`) pass: 529 tests. That includes R6's no-prompt rule and the WAIT/dialog tests.
- I did not run the gate, and `build/land-1.gate.md` records it as `GATE: PASS`.
- Skills' cases can't run in a scratch repo, so R5 is covered only by a stand-in in the tests.
- `grep` finds no "shipped by hand" left in the land `SKILL.md` or the factory README, which matches R14.

## Evidence
$ head -5 .sdlc/work/103*/build/land-1.gate.md; tail -5 ...
GATE: PASS
(attempt 1 verdict PASS; plugin validation "✔ Validation passed")
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_land.py tests/test_skills.py tests/test_factory.py
529 passed in 45.95s
exit: 0

$ uv run --group dev pytest -q tests/test_land.py -k "factory_alone or recovery or carries_drops"
4 passed, 22 deselected in 19.46s
exit: 0

$ grep -n "shipped by hand" plugins/factory/README.md plugins/factory/skills/land/SKILL.md
(no output)
exit: 0 (the pipe ends in `head`)
