# 220-base-ci-red — entries

## [2026-11-22-3] [nit] `_write_ci_cache` formats `checked` by hand with `+00:00`.

Raised by the code review of 220-base-ci-red, round 1: scripts/sdlc.py:9860: `_write_ci_cache` formats `checked` by hand with `+00:00`. The update cache probably has a similar helper, and sharing it would remove the duplicate.

Theme: refactor
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 220-base-ci-red (correctness)

## [2026-11-22-4] [nit] R3 says nothing is written outside a repo, and only the missing-source cases check for a cache file.

Raised by the test review of 220-base-ci-red, round 1: tests/test_base_ci.py: R3 says nothing is written outside a repo, and only the missing-source cases check for a cache file. No test calls `base_ci()` with a home that isn't a repo and asserts it writes nothing.

Theme: tests
Paths: tests/test_base_ci.py
Cost: S
Value: low
Raised by: 220-base-ci-red (correctness)

## [2026-11-22-5] [nit] the `os.replace` temp-file write and `newline="\n"` (R3, R11) are covered only by the existing `tests/test_windows.py` scans, not by a test of this change.

Raised by the test review of 220-base-ci-red, round 1: tests/test_base_ci.py: the `os.replace` temp-file write and `newline="\n"` (R3, R11) are covered only by the existing `tests/test_windows.py` scans, not by a test of this change.

Theme: tests
Paths: tests/test_base_ci.py
Cost: S
Value: low
Raised by: 220-base-ci-red (correctness)
