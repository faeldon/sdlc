I fixed the one kept change, and the gate passes (2250 tests passed, 13 skipped).

- **code C1 (`factory.py`, `_land_diff()` falling back to the base branch's tip):** Done. When `git merge-base <base> HEAD` finds nothing, `_land_diff()` now returns None, and both `land-review` and `land-verify` stop with "no fork point between `<base>` and HEAD: the landing can't be reviewed". The reviewers never get a diff against the moved tip. The message is a new constant, `_NO_FORK`, and the refusal goes out through the same string return `_land_task` already uses for its other refusals.

**Test added:** `test_a_landing_review_with_no_fork_point_is_refused` makes `merge-base` return nothing, then checks that both landing tasks give that refusal instead of a prompt. It failed before the fix and passes after.

**`plan.md`:** the Files section now says both tasks refuse when there is no merge base, and the Tests section lists the new test.

**`notes.md`:** nothing added.

No new decisions. The open default from round 1 still stands: the round's base is read from git when the prompt is built, not recorded.

## Evidence

$ uv run --group dev pytest -q tests/test_land.py -k no_fork_point   (before the fix)
FAILED tests/test_land.py::test_a_landing_review_with_no_fork_point_is_refused
1 failed, 50 deselected in 6.11s
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k "no_fork_point or rounds_own_base"
2 passed, 49 deselected in 2.50s
exit: 0

$ ./check.sh
2250 passed, 13 skipped in 93.49s (0:01:33)
✔ Validation passed
✔ Validation passed
exit: 0
