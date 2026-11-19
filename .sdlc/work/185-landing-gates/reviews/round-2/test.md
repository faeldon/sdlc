VERDICT: PASS

The kept change was made. `checks_clearance()` in `landing.py` now returns `step: "accept"`, `clear: False` and the reason "checks.md is gone, so there is nothing to judge" when `checks_sha(folder)` is None. `_land_task` therefore refuses before `cmd_agent` reaches `checks_sha(folder)[:16]` at `factory.py:4431`.

`test_land_checks_refuses_outside_a_changed_train_change` now has the missing case. It unlinks `checks.md` after the yes and expects the refusal "checks.md is gone". It also asserts no session started and no `land-checks` record was written.

## Notes
- Gate record `build/round-2.gate.md`: `GATE: PASS`, exit 0. I did not read the test count from it.
- Test run: `uv run --group dev pytest tests/test_train.py::test_land_checks_refuses_outside_a_changed_train_change -q` gave 1 passed.
- I checked the new case by reading it and running it. I did not revert the fix to confirm the case fails without it.
- No `checks.md` sections were part of this round's review.
- NIT: plugins/factory/scripts/factory.py:4431: `checks_sha(folder)[:16]` still assumes a non-None value, and only the guard in `_land_task` upstream keeps it safe. {robustness S low}
