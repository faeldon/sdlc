# 196-evidence-and-deleted-conflicts — entries

Retire 2026-11-20-8: taken in by 196-evidence-and-deleted-conflicts
Retire 2026-11-20-9: taken in by 196-evidence-and-deleted-conflicts

## [2026-11-20-19] [nit] a read that printed output and then hits a blank line and a `## Notes` heading with no `exit:` keeps the section open.

Raised by the code review of 196-evidence-and-deleted-conflicts, round 1: plugins/factory/scripts/factory.py:1586: a read that printed output and then hits a blank line and a `## Notes` heading with no `exit:` keeps the section open. Any later `$ ` line in that report is then counted as an evidence command. This is a deliberate trade-off and the docstring says so, but a test pinning that case would make it explicit.

Theme: tests
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 196-evidence-and-deleted-conflicts (correctness)

## [2026-11-20-20] [nit] restrict the missing-file pass to `deleted_sides()` paths so a `UU` file can't silently become a staged deletion

Raised by the security review of 196-evidence-and-deleted-conflicts, round 1: plugins/factory/scripts/landing.py:2827: restrict the missing-file pass to `deleted_sides()` paths so a `UU` file can't silently become a staged deletion

Theme: robustness
Paths: plugins/factory/scripts/landing.py
Cost: S
Value: med
Raised by: 196-evidence-and-deleted-conflicts (contract)

## [2026-11-20-21] [nit] the docstring says a command that owes its `exit:` "never finds it in a later section", but a heading with no blank line before it doesn't end the section

Raised by the security review of 196-evidence-and-deleted-conflicts, round 1: plugins/factory/scripts/factory.py:1569: the docstring says a command that owes its `exit:` "never finds it in a later section", but a heading with no blank line before it doesn't end the section

Theme: docs
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 196-evidence-and-deleted-conflicts (contract)

## [2026-11-20-22] [nit] a read whose printed heading follows a blank line (the `## Speed` line in 189's report) is only covered by the one combined case, so a regression to the blank-line rule would show up only there

Raised by the test review of 196-evidence-and-deleted-conflicts, round 1: tests/test_evidence_headings.py:1: a read whose printed heading follows a blank line (the `## Speed` line in 189's report) is only covered by the one combined case, so a regression to the blank-line rule would show up only there

Theme: tests
Paths: tests/test_evidence_headings.py
Cost: S
Value: low
Raised by: 196-evidence-and-deleted-conflicts (correctness)
