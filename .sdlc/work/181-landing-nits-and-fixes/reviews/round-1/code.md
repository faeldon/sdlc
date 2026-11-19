VERDICT: PASS

## Notes
- R1–R3: `named_nits()` now reads only `Nits taken in:` lines through the new `taken_lines()`. It keeps its signature and register order. All three callers change together, because they all go through `named_nits()`.
- R5–R7, R9: `cmd_land_fix` refuses an empty fix unless `_not_already_made()` finds the `FIX: ALREADY MADE` answer and passing evidence. It then makes no commit and marks the train's fix done. The ask file is untouched, so the fix is still a signal.
- R4 and R10 prose changes are in place. I read the diff and the tests named for R1–R3, R5–R7 and R9, not the R4, R8 or R10 test bodies.
- I did not review `tests/test_train.py`, `tests/test_prompts.py`, `tests/test_skills.py` or the skill prose line by line. The gate record covers them: attempt 2 is PASS, after attempt 1 failed in `tests/test_adoption.py` (the failing line was not in the output I read).
- Done well: the failure goes in the safe direction, so a nit with no marker stays open. `FIX_RE` takes any `FIX:` answer, so `opening()` treats two lines that disagree as no answer.
- Ran the 4 tests that match `already_made`, `taken_in` or `named_but` in `tests/test_land.py`, in the foreground. They passed.
- NIT: plugins/factory/scripts/landing.py:1420: the refusal message is long and repeats `FIX: ALREADY MADE` {style S low}
