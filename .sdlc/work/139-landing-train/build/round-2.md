Both KEPT changes are addressed, the gate is green, and nothing is committed (`HEAD` still `e111ebc`; the same 14 paths as round 1 are changed or new, the stray directory a test fake left is gone).

## Report — 139 landing-train, rework round 1

**KEPT changes**

- **C1 (R14's handoff half untested).** Two tests in `tests/test_train.py`:
  - `test_a_close_that_hands_off_runs_under_the_parents_hold`: a copy of the plugin's files in a scratch repo, a change that edits `scripts/`, shipped and closed through `uv run --script` so main's script runs the close, holds the lock from its merge and hands the rest to the merged code; asserted to finish (timeout 600 s), `ran: merged code`, `remove folder` in `done`, and the first-parent line. Were `_handoff()` to stop passing the variable, the child would wait on the parent's lock and the timeout would fail it.
  - `test_the_handoff_passes_the_hold_and_the_child_takes_no_lock` (portable): `_handoff()` passes `SDLC_LOCK_HELD=<lock path>` only while this process holds the lock; a `cmd_close()` told so runs to its end while another thread holds the OS lock; the variable is gone from `os.environ` after; and every `subprocess.run` the close made saw no such variable. That last assertion found a real gap: `cmd_close()` popped the variable *after* `main_root()`'s git call, so the first subprocess carried it. The pop is now the function's first act (`scripts/sdlc.py`).
- **C2 (R8's other causes untested).** Two train tests: `test_failing_acceptance_checks_as_stacked_eject_only_that_change` (change 2's check `test ! -f aa.txt` passes before the train and fails once stacked on change 1; `accept` reruns on the stacked commit, 2 alone is ejected with `build/land-accept.md` named, its record showing both attempts; 1 and 3 land) and `test_a_reply_still_unreadable_after_its_mend_ejects_only_that_change` (change 2's behaviour reply puts its verdict after a preamble, is mended once and does it again; the round stops, 2 alone is ejected, `runs/mended` in its commit reads `behaviour land-1`; 1 and 3 land). The driver `_drive()` now runs a `commit`'s `before` steps and takes a `mend` step with a hook.

Both C2 tests and the real-handoff test exercise behaviour built in round 1 and passed once their test-side slips were fixed; the mechanics test is the one that went red for a reason in the code. `plan.md`'s test list and departures section record all of this. No `- DROPPED:` lines were acted on. No new decisions.

## Evidence

```
$ ./check.sh > /tmp/gate-139-r1.txt 2>&1; echo "exit: $?"; grep -E "passed|failed|error|Validation" /tmp/gate-139-r1.txt | tail -6
exit: 0
All checks passed!
2569 passed, 18 skipped in 93.57s (0:01:33)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest tests/test_train.py -q -p no:cacheprovider; echo "exit: $?"
21 passed in 115.75s (0:01:55)
exit: 0

$ uv run --group dev pytest -q -m portable -p no:cacheprovider; echo "exit: $?"
461 passed, 18 skipped, 2108 deselected in 105.23s (0:01:45)
exit: 0

$ uv run --group dev pytest tests/test_train.py -q -p no:cacheprovider -k "hands_off or passes_the_hold or acceptance_checks_as_stacked or still_unreadable"
FAILED tests/test_train.py::test_the_handoff_passes_the_hold_and_the_child_takes_no_lock
1 failed, 3 passed, 17 deselected in 19.88s
exit: 1
(before the pop moved ahead of main_root(): "no subprocess of the close saw the variable" — the first git call carried it)

$ uv run --group dev pytest tests/test_train.py -q -p no:cacheprovider -k "passes_the_hold"
1 passed, 20 deselected in 0.55s
exit: 0

$ uv run --group dev ruff check scripts/sdlc.py tests/test_train.py
All checks passed!
exit: 0

$ git log --oneline -1; git status --porcelain | wc -l
e111ebc File 2026-11-18-40
      14
```
