# 169-decisions-and-stops-counted — entries

Retire 2026-11-18-86: taken in by 169-decisions-and-stops-counted
Retire 2026-11-18-87: taken in by 169-decisions-and-stops-counted

## [2026-11-19-19] [nit] `autonomy_counts` counts a ledger line with the `SUPERSEDED` and `SETTLED` marks under `defaults` only.

Raised by the code review of 169-decisions-and-stops-counted, round 1: scripts/factory_records.py:643: `autonomy_counts` counts a ledger line with the `SUPERSEDED` and `SETTLED` marks under `defaults` only. A superseded or settled blocking or look line gets no such check. It falls under answered or checked, which is probably right, since the approver settles defaults only. A one-line comment would make that explicit

Theme: docs
Paths: scripts/factory_records.py
Cost: S
Value: low
Raised by: 169-decisions-and-stops-counted (correctness)

## [2026-11-19-20] [nit] R8's rate test lets one ledger give `kept=1, changed=1`, so `kept/(kept+changed)` and `kept/total_defaults` can't be told apart by the 0.5 rate alone.

Raised by the test review of 169-decisions-and-stops-counted, round 1: tests/test_retro.py:2606: R8's rate test lets one ledger give `kept=1, changed=1`, so `kept/(kept+changed)` and `kept/total_defaults` can't be told apart by the 0.5 rate alone. A test with `confirmed` or `settled` lines that outnumber the rest would fail if the denominator changed.

Theme: tests
Paths: tests/test_retro.py
Cost: S
Value: low
Raised by: 169-decisions-and-stops-counted (correctness)
