# 174-waste-tagged — entries

Retire 2026-11-19-16: taken in by 174-waste-tagged
Retire 2026-11-19-22: taken in by 174-waste-tagged

## [2026-11-19-35] [nit] `_cost()` runs once in `retro()` and again in `retro_report()`, and each run re-reads every change's commit.

Raised by the code review of 174-waste-tagged, round 1: scripts/retro.py:1752: `_cost()` runs once in `retro()` and again in `retro_report()`, and each run re-reads every change's commit. Computing it once per `retro` call would halve the git reads.

Theme: refactor
Paths: scripts/retro.py
Cost: M
Value: low
Raised by: 174-waste-tagged (correctness)

## [2026-11-19-36] [nit] if `claude` returns no figures, no row is written, so a run that failed that way doesn't make the next try a `rerun`.

Raised by the code review of 174-waste-tagged, round 1: plugins/factory/scripts/factory.py:4392: if `claude` returns no figures, no row is written, so a run that failed that way doesn't make the next try a `rerun`. This matches R3 as worded. A line in the `purpose_of()` docstring would say so.

Theme: docs
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 174-waste-tagged (correctness)

## [2026-11-19-37] [nit] R1's `land` field is never asserted on a row written by `cmd_agent` for a landing task.

Raised by the test review of 174-waste-tagged, round 1: tests/test_factory.py: R1's `land` field is never asserted on a row written by `cmd_agent` for a landing task. `purpose_of` is tested for it, but no test runs a `land-review` through `cmd_agent` and checks the row carries `land`.

Theme: tests
Paths: tests/test_factory.py
Cost: S
Value: low
Raised by: 174-waste-tagged (correctness)

## [2026-11-19-38] [nit] the stop half of `test_an_ejection_is_recorded_and_amended_in` doesn't check `at` or `land` on its rows.

Raised by the test review of 174-waste-tagged, round 1: tests/test_train.py: the stop half of `test_an_ejection_is_recorded_and_amended_in` doesn't check `at` or `land` on its rows. Only `cause` is asserted.

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 174-waste-tagged (correctness)
