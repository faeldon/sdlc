VERDICT: PASS

Both changes kept last round were made, and the full suite passes.

## Notes
- **R14, the lock handoff (kept change made):** `test_the_handoff_passes_the_hold_and_the_child_takes_no_lock` covers it.
  - `_handoff()` puts `LOCK_HELD_ENV` in the child's environment only while this process holds the lock, and sets `HANDOFF_ENV` to `merged`. Dropping the variable fails the assertion at line 249.
  - A real `cmd_close` run while another thread holds the OS lock finishes within the 60-second timeout, so it did not deadlock.
  - After the close, the variable is gone from `os.environ`, and none of the close's own subprocesses saw it.
- **R8, ejection of only the failing change (kept change made):** three tests now cover it. In each, change 2 is ejected and changes 1 and 3 land, with two `Close` commits on the first-parent line.
  - `test_a_kept_landing_change_ejects_only_its_change` covers a landing review that keeps a change. The ejected change goes back to its old base.
  - `test_failing_acceptance_checks_as_stacked_eject_only_that_change` covers a check that passes on the change's own base but fails once stacked on change 1. The check runs again on the stacked commit, and the `ACCEPT: FAIL` record holds two attempts.
  - `test_a_reply_still_unreadable_after_its_mend_ejects_only_that_change` covers a reply that stays unreadable after the one mend. It is mended once and then ejected.
- No `checks.md` sections were added by the change itself. The only `checks.md` in the tests is the fixture inside the acceptance-check test.
- Tests run:
  - `uv run --group dev pytest tests/test_train.py -q -n auto`: 21 passed.
  - `uv run --group dev pytest -q -n auto`: 2569 passed, 18 skipped.
