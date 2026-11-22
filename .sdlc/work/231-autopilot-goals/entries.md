# 231-autopilot-goals — entries

## [2026-11-22-32] [nit] say to single-quote a goal given in the person's own words, so `$`, backticks and `"` in it stay literal

Raised by the security review of 231-autopilot-goals, round 1: plugins/factory/skills/autopilot/SKILL.md:101: say to single-quote a goal given in the person's own words, so `$`, backticks and `"` in it stay literal

Theme: robustness
Paths: plugins/factory/skills/autopilot/SKILL.md
Cost: S
Value: med
Raised by: 231-autopilot-goals (contract)

## [2026-11-22-33] [nit] the "empty reason" case rewrites the WAITS line to a bare reason; no case gives a WAVE or LEAVE line an empty reason, which R8 also names

Raised by the test review of 231-autopilot-goals, round 1: tests/test_autopilot.py:1735: the "empty reason" case rewrites the WAITS line to a bare reason; no case gives a WAVE or LEAVE line an empty reason, which R8 also names

Theme: tests
Paths: tests/test_autopilot.py
Cost: S
Value: low
Raised by: 231-autopilot-goals (correctness)

## [2026-11-22-34] [nit] no case puts a `LEAVE` heading-less before any group to show LEAVE is allowed anywhere.

Raised by the test review of 231-autopilot-goals, round 1: tests/test_autopilot.py:1696: no case puts a `LEAVE` heading-less before any group to show LEAVE is allowed anywhere. Only the group-less WAVE case exists.

Theme: tests
Paths: tests/test_autopilot.py
Cost: S
Value: low
Raised by: 231-autopilot-goals (correctness)
