# 177-indicators-structured — entries

## [2026-11-19-39] [idea] Reject indicator names and units that don't read back from the report

Left undone by 177-indicators-structured, carried forward when it landed: A `unit` that is literally `—`, or a `name` or `unit` with leading or trailing spaces, is accepted by `host_rows()` but reads back from the report as a different key (`""`, or stripped), so it gets no `last`. R1 doesn't forbid either; rejecting them would be a one-line rule in `host_rows()` if it ever matters.
See .sdlc/work/177-indicators-structured/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-40] [nit] R2's OSError case has no test; `_indicator_rows` treats it like the timeout path

Raised by the test review of 177-indicators-structured, round 1: tests/test_retro.py:1957: R2's OSError case has no test; `_indicator_rows` treats it like the timeout path

Theme: tests
Paths: tests/test_retro.py
Cost: S
Value: low
Raised by: 177-indicators-structured (correctness)
