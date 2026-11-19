Round 1 is fixed: the one kept change and the security nit are both done, and the full gate passes (3386 passed, 29 skipped).

- **KEPT, code (`factory.py:4431`):** if `checks.md` was deleted after `--begin`, a hand-run `agent --task land-checks` crashed on `None[:16]`. I took the reviewer's first fix: `checks_clearance()` now stops at `accept`, not clear, when `checks.md` is gone, saying `checks.md is gone, so there is nothing to judge`. So `_land_task` refuses before any session starts. I removed the old `sha is None` test from the record check, since that case now returns earlier. I added a case to `test_land_checks_refuses_outside_a_changed_train_change`: delete `checks.md`, then expect that refusal and no session. It failed with the `TypeError` before the fix.
- **Nit, security (`landing.py:866`):** the read-only list now refuses grep's options that follow symlinks while it searches folders: `-R`, `--dereference-recursive`, and the BSD `-S` and `-O`, alone or bundled (`-rnS`). Plain `-r` still passes, because the existing path rule already checks the paths named on the command line. Four refusal cases and one passing case (`grep -rn -e keep src`) were added to the R5 tests. The four refusals failed before the fix.

`plan.md` is unchanged and nothing new went into `notes.md`.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_train.py -k "read_only or land_checks_refuses"  (before the fix)
E       AssertionError: ('grep -R keep .', None)
E       TypeError: 'NoneType' object is not subscriptable
FAILED tests/test_train.py::test_read_only_command[grep -R keep .--R]
exit: 1

$ uv run --group dev pytest -q tests/test_train.py -k "read_only or land_checks_refuses or approvers_answer or harmless_never"
59 passed, 77 deselected in 21.26s
exit: 0

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 185
All checks passed!
3386 passed, 29 skipped in 288.05s (0:04:48)
✔ Validation passed
exit: 0
