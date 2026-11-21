VERDICT: PASS

I found no failure. A train of one is now gated at its committed tip, and the 13 tests for it pass. I did not run the end-to-end path by hand. The spec names no command beyond the tests, so I ran the named tests instead.

## Notes
- **`checks.md`:** the change has none, so there is nothing to read or run.
- **Fix:** `_train_gate()` no longer returns early for `m == 1 and stacked == pre`. A one-change train now reads `next: gate`, and a red tip ejects the change.
- **`ungated`:** the train reading and `_run_end()` now carry `ungated`, set only when the base branch names no `[commands] check`. `land_question` and `cmd_land_check` say "not gated, since <base> names no [commands] check" in that case. So the question's "gated once at the tip" holds whenever a check exists.
- **Docs:** the land skill's Step 3 and Step 4 text covers the gate and `ungated`.
- **Suite result:** the gate record `build/round-1.gate.md` reads `GATE: PASS`, exit 0.
- **Cosmetic:** one line in the land skill's Step 4 text runs well past the file's usual width. It does not affect any behaviour.

## Evidence
$ git diff HEAD --stat | tail -3
 tests/test_skills.py                 |  10 +++
 tests/test_train.py                  | 115 +++++++++++++++++++++++++++++++++--
 7 files changed, 201 insertions(+), 30 deletions(-)
exit: 0

$ git diff HEAD -- plugins/factory/scripts/landing.py plugins/factory/skills/land/SKILL.md
(the diff showed `_train_gate`'s early return removed, `_ungated()` added, `ungated` put into the reading and the run's end summary, `land_question(..., gated)` reworded, and the land skill's text updated)
exit: 0

$ head -12 .sdlc/work/217-train-gates-every-tip/build/round-1.gate.md
GATE: PASS
Verdict: PASS
Command: ./check.sh
Exit: 0
exit: 0

$ ls .sdlc/work/217-train-gates-every-tip/checks.md
ls: no such file
exit: 1

$ uv run --group dev pytest -q tests/test_train.py -k "train_of_one or no_check or hand_written or records_its_tip or tip_gate or red_one" tests/test_land.py
13 passed, 268 deselected in 131.60s (0:02:11)
exit: 0
