# 199-landing-records-unforgeable — entries

## [2026-11-20-58] [nit] `_vouch()` calls `closing._unlock` but `_try_lock` from the local module.

Raised by the code review of 199-landing-records-unforgeable, round 1: scripts/sdlc.py:3283: `_vouch()` calls `closing._unlock` but `_try_lock` from the local module. Both work, but a one-line comment would say why the pair is split.

Theme: docs
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 199-landing-records-unforgeable (correctness)

## [2026-11-20-59] [nit] the spec's R9 requires a test of two writers at once.

Raised by the code review of 199-landing-records-unforgeable, round 1: tests/test_records_ledger.py: the spec's R9 requires a test of two writers at once. One exists (`test_two_writers_at_once_leave_whole_lines`), but it only covers `factory.py`'s writer and not core's copy under the same lock.

Theme: tests
Paths: tests/test_records_ledger.py
Cost: S
Value: low
Raised by: 199-landing-records-unforgeable (correctness)

## [2026-11-20-60] [nit] "An agent editing the change's worktree can't forge one" overstates the protection when the builder and resolver have Bash.

Raised by the security review of 199-landing-records-unforgeable, round 1: plugins/factory/README.md: "An agent editing the change's worktree can't forge one" overstates the protection when the builder and resolver have Bash. Say that it protects against the Edit and Write tools, not against a shell that can reach the git common dir

Theme: docs
Paths: plugins/factory/README.md
Cost: S
Value: med
Raised by: 199-landing-records-unforgeable (contract)

## [2026-11-20-61] [nit] check again that `earlier` is vouched when it's read after the run, not only before the slot wait

Raised by the security review of 199-landing-records-unforgeable, round 1: plugins/factory/scripts/factory.py:3358: check again that `earlier` is vouched when it's read after the run, not only before the slot wait

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: med
Raised by: 199-landing-records-unforgeable (contract)

## [2026-11-20-62] [nit] the writer test runs 400 locked appends across two processes, which may be slow on a loaded machine; a smaller count would still prove whole lines

Raised by the test review of 199-landing-records-unforgeable, round 1: tests/test_records_ledger.py:152: the writer test runs 400 locked appends across two processes, which may be slow on a loaded machine; a smaller count would still prove whole lines

Theme: tests
Paths: tests/test_records_ledger.py
Cost: S
Value: low
Raised by: 199-landing-records-unforgeable (correctness)
