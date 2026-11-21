# 219-closes-at-start — entries

Retire 2026-11-20-47: taken in by 219-closes-at-start

## [2026-11-22-1] [nit] `recorded_closes()` reads the whole ledger on every call, and `record_closes()` calls it on every agent run.

Raised by the code review of 219-closes-at-start, round 1: plugins/factory/scripts/factory.py:3181: `recorded_closes()` reads the whole ledger on every call, and `record_closes()` calls it on every agent run. The ledger is small, so the cost is negligible.

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 219-closes-at-start (correctness)

## [2026-11-22-2] [nit] in `cmd_agent`, `_record_land()` runs before `record_closes()`, so if the ledger append fails, the landing step is recorded for an agent that is then refused.

Raised by the security review of 219-closes-at-start, round 1: plugins/factory/scripts/factory.py:5095: in `cmd_agent`, `_record_land()` runs before `record_closes()`, so if the ledger append fails, the landing step is recorded for an agent that is then refused. Recording `closes:` first would make the refusal leave nothing behind.

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 219-closes-at-start (contract)
