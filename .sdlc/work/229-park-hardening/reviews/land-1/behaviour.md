VERDICT: PASS

The change does what its intent says, and the two checks should pass. I ran the four test files that cover the change (426 passed, 28 skipped). The repo's gate record for this round (`land-1`) says PASS.

## Notes
- **Park exit and busy lines:** `_park()` now refuses a `[park] exit` of 0 or 1 with a warning, and nothing parks. `busy_of()` strips C0 and C1 control characters. Both are covered by the new tests in `tests/test_factory_park.py`.
- **`park --clear`:** it now removes a record the ledger never vouched for, as decision D2 settled.
- **Board and `status`:** `needs_of()` and the board now cut the park's deadline by the base branch's `[park] deadline`, through `_park_deadline_at()` and `capped_park()`, as `verdicts` does. Tests in `tests/test_board.py`, `tests/test_hand_gate.py` and `tests/test_modules.py` pin the new copies to `factory.py`'s.
- **Checks in `checks.md`:** I read both and expect both to pass. I ran only their two `grep` assertions; the check commands themselves I did not run.
  - "AGENTS.md's Skills list names update": the `grep` matches line 366 of `AGENTS.md`, which now lists `update`.
  - "The factory README says 75 is the exit to use": the `grep` matches the `[park]` block's comment in `plugins/factory/README.md`.
- **Not run:** I did not run the whole suite or any check command. The gate record covers the suite. The record has no `exit:` line, so my first `grep "exit:"` on it printed nothing.

## Evidence
$ head -5 .sdlc/work/229-park-hardening/build/land-1.gate.md
GATE: PASS

## Attempt 1

Verdict: PASS
exit: 0

$ grep -n "exit:" .sdlc/work/229-park-hardening/build/land-1.gate.md | head -3
exit: 0

$ uv run --group dev pytest -q tests/test_factory_park.py tests/test_board.py tests/test_hand_gate.py tests/test_modules.py -n auto 2>&1 | tail -5
426 passed, 28 skipped in 33.73s
exit: 0

$ grep -q 'Skills that write (`intent`, `spec`, `ship`, `close`, `drop`, `update`,' AGENTS.md; echo agents $?
agents 0
exit: 0

$ grep -q '75 (EX_TEMPFAIL) is the one to use' plugins/factory/README.md; echo readme $?
readme 0
exit: 0
