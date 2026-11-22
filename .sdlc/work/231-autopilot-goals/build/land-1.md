`tests/test_autopilot.py` is resolved, and its 78 tests pass. I ran that file alone, not the full suite.

## What I did

**The conflict.** Both sides appended a block at the end of the file. I kept both and removed the markers:
- 228's block, "the whole loop, as it runs" (the end-to-end test through real subprocesses).
- 231's block, "a run toward a goal" (`DIRECTION`, the goal tests and `test_the_skill_quotes_the_preview_question`).

**Two tests broke once the changes were stacked.** Neither side had a conflict marker there. I made the smallest change to each 228 test so it satisfies 231's new rules, without touching what 228 asserts:
- **`test_no_ledger_writer_runs_beside_another_step_of_its_change` (228 R5):**
  - The cause was the wave replies, written as raw `- WAVE:` strings.
  - 231's planner now has to place every candidate, so those raw replies were refused and no change was opened.
  - I changed them to `[[S1, S3], []]`, the form 231's `Steps` turns into a full plan through `_plan_reply`.
- **`test_autopilot_run_lands_a_seed_through_real_subprocesses` (228 R1/R2):**
  - 231's `--begin` refuses to run without a goal, so I added `--goal "Keep drafts working"`.
  - The stand-in planner's reply is now a plan 231 accepts: a `##` heading, then `- WAVE: <seed> — tier 1 — <reason>`. It is a new `PLAN` constant.
  - The later `NONE` reply is unchanged.

`ruff format` also reformatted the file, and `ruff check` passes.

## Noticed and left alone
Nothing else.

## Evidence

$ grep -n '^<<<<<<<\|^=======\|^>>>>>>>' tests/test_autopilot.py
(no output; 0 markers after the fix)
exit: 1

$ uv run --quiet --group dev ruff format tests/test_autopilot.py
1 file reformatted
exit: 0

$ uv run --quiet --group dev pytest -q tests/test_autopilot.py -n auto
78 passed in 17.85s
exit: 0

$ uv run --quiet --group dev ruff check tests/test_autopilot.py
All checks passed!
exit: 0
