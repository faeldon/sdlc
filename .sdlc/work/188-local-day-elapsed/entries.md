# 188-local-day-elapsed — entries

## [2026-11-20-4] [nit] the `east` fixture uses `time.tzset()`, which doesn't exist on Windows.

Raised by the code review of 188-local-day-elapsed, round 1: tests/test_archive.py:2500: the `east` fixture uses `time.tzset()`, which doesn't exist on Windows. That is fine as long as these tests stay unmarked `portable`, but a comment saying so would stop someone adding the marker later.

Theme: tests
Paths: tests/test_archive.py
Cost: S
Value: low
Raised by: 188-local-day-elapsed (correctness)
