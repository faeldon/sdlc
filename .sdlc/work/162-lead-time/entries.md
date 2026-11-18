# 162-lead-time — entries

## [2026-11-19-1] [nit] `lead_time()` returns `{}` when `opened` is after `closed`, and the code files that as `lead=bad-opened`.

Raised by the code review of 162-lead-time, round 1: scripts/closing.py:474: `lead_time()` returns `{}` when `opened` is after `closed`, and the code files that as `lead=bad-opened`. That word is meant for an unparsable `opened:`. A clock that ran backwards is a different case; a distinct word such as `lead=clock` would say which one it was.

Theme: docs
Paths: scripts/closing.py
Cost: S
Value: low
Raised by: 162-lead-time (correctness)

## [2026-11-19-2] [nit] a factory change with no timed rows and no transcript events gets `ready=None`, so `ready_wait` is dropped (`source=git`).

Raised by the code review of 162-lead-time, round 1: scripts/closing.py:431: a factory change with no timed rows and no transcript events gets `ready=None`, so `ready_wait` is dropped (`source=git`). R10's "no transcripts" case says `lead`, `ready_wait` and `landing` are kept. The code is reasonable, because there is no approver row to read `ready` from. The spec could say so, or `ready` could fall back to the tip's author date for a factory change too.

Theme: robustness
Paths: scripts/closing.py
Cost: S
Value: low
Raised by: 162-lead-time (correctness)

## [2026-11-19-3] [nit] the broad `except Exception` also hides programming errors as `lead=failed`.

Raised by the security review of 162-lead-time, round 1: scripts/closing.py:475: the broad `except Exception` also hides programming errors as `lead=failed`. That fits "never refuses", but it could log the exception's type name to stderr so a regression is visible

Theme: robustness
Paths: scripts/closing.py
Cost: S
Value: low
Raised by: 162-lead-time (contract)

## [2026-11-19-4] [nit] the `lead=bad-opened` path for `opened` after `closed` (decision D3) has no test of its own; only a malformed value is parametrized

Raised by the test review of 162-lead-time, round 1: tests/test_archive.py: the `lead=bad-opened` path for `opened` after `closed` (decision D3) has no test of its own; only a malformed value is parametrized

Theme: tests
Paths: tests/test_archive.py
Cost: S
Value: low
Raised by: 162-lead-time (correctness)
