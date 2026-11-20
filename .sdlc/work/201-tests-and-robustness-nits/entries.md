# 201-tests-and-robustness-nits — entries

Retire 2026-11-19-8: taken in by 201-tests-and-robustness-nits
Retire 2026-11-19-7: taken in by 201-tests-and-robustness-nits
Retire 2026-11-19-11: taken in by 201-tests-and-robustness-nits
Retire 2026-11-19-17: taken in by 201-tests-and-robustness-nits
Retire 2026-11-19-20: taken in by 201-tests-and-robustness-nits
Retire 2026-11-19-23: taken in by 201-tests-and-robustness-nits
Retire 2026-11-19-29: taken in by 201-tests-and-robustness-nits
Retire 2026-11-19-38: taken in by 201-tests-and-robustness-nits
Retire 2026-11-19-40: taken in by 201-tests-and-robustness-nits
Retire 2026-11-19-49: taken in by 201-tests-and-robustness-nits
Retire 2026-11-19-51: taken in by 201-tests-and-robustness-nits
Retire 2026-11-19-55: taken in by 201-tests-and-robustness-nits
Retire 2026-11-19-56: taken in by 201-tests-and-robustness-nits
Retire 2026-11-19-57: taken in by 201-tests-and-robustness-nits
Retire 2026-11-19-67: taken in by 201-tests-and-robustness-nits
Retire 2026-11-19-73: taken in by 201-tests-and-robustness-nits
Retire 2026-11-19-76: taken in by 201-tests-and-robustness-nits
Retire 2026-11-19-77: taken in by 201-tests-and-robustness-nits
Retire 2026-11-20-2: taken in by 201-tests-and-robustness-nits
Retire 2026-11-20-4: taken in by 201-tests-and-robustness-nits
Retire 2026-11-20-16: taken in by 201-tests-and-robustness-nits
Retire 2026-11-20-10: taken in by 201-tests-and-robustness-nits
Retire 2026-11-20-22: taken in by 201-tests-and-robustness-nits
Retire 2026-11-20-26: taken in by 201-tests-and-robustness-nits
Retire 2026-11-20-29: taken in by 201-tests-and-robustness-nits
Retire 2026-11-20-30: taken in by 201-tests-and-robustness-nits
Retire 2026-11-20-32: taken in by 201-tests-and-robustness-nits
Retire 2026-11-20-33: taken in by 201-tests-and-robustness-nits
Retire 2026-11-20-34: taken in by 201-tests-and-robustness-nits

## [2026-11-20-54] [nit] `BUILT_IN` is a hand-kept list, and the check reads `node.args.args` only, so a keyword-only fixture is missed.

Raised by the code review of 201-tests-and-robustness-nits, round 1: tests/test_suite_shape.py:12: `BUILT_IN` is a hand-kept list, and the check reads `node.args.args` only, so a keyword-only fixture is missed. Reading `kwonlyargs` too is a one-line fix

Theme: tests
Paths: tests/test_suite_shape.py
Cost: S
Value: low
Raised by: 201-tests-and-robustness-nits (correctness)

## [2026-11-20-55] [nit] the plan promises a line naming the test that settles each of the 20 nits 191 already fixed.

Raised by the code review of 201-tests-and-robustness-nits, round 1: .sdlc/work/201-tests-and-robustness-nits/notes.md: the plan promises a line naming the test that settles each of the 20 nits 191 already fixed. I only confirmed that `notes.md` exists (74 lines) and did not check that all 20 are covered

Theme: docs
Paths: .sdlc/work/201-tests-and-robustness-nits/notes.md
Cost: S
Value: low
Raised by: 201-tests-and-robustness-nits (context)
