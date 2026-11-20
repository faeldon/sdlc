# 202-defaults-to-landing — entries

## [2026-11-20-46] [nit] `uncarried()` reports `named` (an id in both SETTLED and CONFIRM) only when the id is also CONFIRMed.

Raised by the code review of 202-defaults-to-landing, round 1: plugins/factory/scripts/run_state.py:104: `uncarried()` reports `named` (an id in both SETTLED and CONFIRM) only when the id is also CONFIRMed. A default that is open and listed as SETTLED but not ticked, because `decisions` was skipped or refused it, reads as "no `- CONFIRM:` line". The mend text then points the approver at the wrong fix. Naming the SETTLED line in that case would be clearer.

Theme: robustness
Paths: plugins/factory/scripts/run_state.py
Cost: S
Value: low
Raised by: 202-defaults-to-landing (correctness)

## [2026-11-20-47] [nit] `intent_closes()` reads `closes:` from the branch's own intent.md while the sensitive bar is read from the base branch; read it from the fork point so a build can't widen what it may carry

Raised by the security review of 202-defaults-to-landing, round 1: plugins/factory/scripts/factory.py:1973: `intent_closes()` reads `closes:` from the branch's own intent.md while the sensitive bar is read from the base branch; read it from the fork point so a build can't widen what it may carry

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 202-defaults-to-landing (contract)

## [2026-11-20-48] [nit] the "closes" case writes `closes: [12]` by string-replacing `idea:` in `intent.md`.

Raised by the test review of 202-defaults-to-landing, round 1: tests/test_factory_decisions.py:523: the "closes" case writes `closes: [12]` by string-replacing `idea:` in `intent.md`. If the fixture's frontmatter changes, the case could pass without exercising the `closes:` rule, though the assertion on `closes: [12]` in the problem text would still catch that.

Theme: tests
Paths: tests/test_factory_decisions.py
Cost: S
Value: low
Raised by: 202-defaults-to-landing (correctness)
