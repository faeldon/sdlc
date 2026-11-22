# 225-ci-pin-test-quotes — entries

Retire 2026-11-22-6: taken in by 225-ci-pin-test-quotes
Retire 2026-11-22-7: taken in by 225-ci-pin-test-quotes
Retire 2026-11-22-8: taken in by 225-ci-pin-test-quotes
Retire 2026-11-22-9: taken in by 225-ci-pin-test-quotes
Retire 2026-11-22-10: taken in by 225-ci-pin-test-quotes

## [2026-11-22-18] [nit] `QUOTED` is a module-level regex used only in `unpinned()`.

Raised by the code review of 225-ci-pin-test-quotes, round 1: tests/test_ci.py:20: `QUOTED` is a module-level regex used only in `unpinned()`. That matches the file's own `USES`, `PINNED` and `VERSION` pattern, so there is nothing to change.

Theme: style
Paths: tests/test_ci.py
Cost: S
Value: low
Raised by: 225-ci-pin-test-quotes (correctness)
