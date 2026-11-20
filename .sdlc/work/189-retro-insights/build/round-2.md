The draft-kept-on-failure case now has a test, and the full gate passes: 3464 passed, 29 skipped, ruff clean, validation passed.

## Kept changes

- **KEPT (test: a failed `git` step leaves the draft): done.** I added `test_a_failed_commit_leaves_the_insights_draft_for_a_rerun` to `tests/test_retro.py`.
  - **How the commit is made to fail:** a real `pre-commit` hook that exits 1. The reviewer suggested stubbing `sdlc._git`, but that wouldn't fail anything: `cmd_retro_commit()` makes its commit through `subprocess.run`, not `sdlc._git`.
  - **What it asserts:**
    - `retro-commit` exits 1 with a `git commit failed` refusal.
    - The draft is still on disk, `HEAD` hasn't moved, and no report is left behind.
    - Once the hook is gone, a rerun commits, removes the draft, and the report shows `### Speed: …` under Insights.
  - **It can fail:** I temporarily added a line deleting the draft before the commit. The test failed (exit 1), and I then restored `scripts/retro.py` from a copy; a grep confirms the temporary line is gone.

No code changed this round, only the one new test, so `plan.md`'s Tests section doesn't name it yet. `notes.md` still holds the one unticked lead-time-by-way line from round 0.

No new decisions this round. The two `[default]` decisions from round 0 stand.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_retro.py -k "failed_commit_leaves"
1 passed, 252 deselected in 2.75s
exit: 0

$ uv run --group dev pytest -q tests/test_retro.py -k "failed_commit_leaves"   # with the draft removed before the commit
1 failed, 252 deselected in 8.67s
exit: 1

$ grep -c MUTANT scripts/retro.py   # after restoring from the copy
0
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py -k "failed_commit_leaves or insight or not_answered"
11 passed, 242 deselected in 3.32s
exit: 0

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
327 files already formatted
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 189
All checks passed!
327 files already formatted
3464 passed, 29 skipped in 156.01s (0:02:36)
✔ Validation passed
✔ Validation passed
exit: 0
