I made the one kept fix: the kill test now waits up to 120 s for the stand-in reviewer to start, instead of 60 s. Run alone, it passed in 26.57 s. I didn't run the full suite, since the gate reruns it on this rework.

- **behaviour, C1 (`tests/test_train.py:1770`):** `test_a_killed_train_run_resumes` now uses a 120 s `time.monotonic()` deadline, polled every 0.05 s as before. That matches the 120 s of the original loop and of the sibling helper `_killed_at_its_gate`. A short poll already makes the test end as soon as the reviewer's `.started` flag appears, so the wider deadline only matters when the machine is slow. A comment on the line says why. This round's reviewer couldn't reproduce the failure (it passed in about 44 s for them) but kept the change anyway, since it costs nothing when the test passes.

`plan.md`'s R14 line now says the wait is 120 s and why it isn't the spec's 60 s. Nothing new went into `notes.md`.

- DECISION: [default] R14's deadline is 120 s, not the spec's 60 s. Going ahead with 120 s unless told otherwise.
  - OPTION: 120 s — fits a loop's startup under load, as a gate shared with other builds has; a real hang takes a minute longer to fail
  - OPTION: 60 s, as the spec says — fails faster on a real hang; failed falsely in round 1 when the loop started slowly under load
  - WHY: the behaviour review's failed run used up the 60 s deadline before the reviewer started, while the same test passes at the merge base with its old 120 s wait.

## Evidence

$ uv run --group dev ruff check tests/test_train.py
All checks passed!
exit: 0

$ uv run --group dev ruff format --check tests/test_train.py
1 file already formatted
exit: 0

$ uv run --group dev pytest -q tests/test_train.py::test_a_killed_train_run_resumes
1 passed in 26.57s
exit: 0
