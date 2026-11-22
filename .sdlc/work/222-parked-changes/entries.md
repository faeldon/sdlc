# 222-parked-changes — entries

## [2026-11-22-13] [nit] `needs_of()` compares `now` with the park's own `DEADLINE`, not the deadline cut to the base branch's `[park] deadline` that `verdicts` uses.

Raised by the code review of 222-parked-changes, round 1: scripts/sdlc.py:5164: `needs_of()` compares `now` with the park's own `DEADLINE`, not the deadline cut to the base branch's `[park] deadline` that `verdicts` uses. A forged record with a far deadline would show no need on the board, while `verdicts` would already stop it. R16 only asks for a need when a supervisor died, so this is cosmetic. Cap it with `capped_park()` in the callers, or accept it.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 222-parked-changes (correctness)

## [2026-11-22-14] [nit] `park --clear` checks only expiry, not `vouched`.

Raised by the code review of 222-parked-changes, round 1: plugins/factory/scripts/factory.py:4034: `park --clear` checks only expiry, not `vouched`. `verdicts` reports an unvouched but parseable record as "remove it, then rerun", while `--clear` refuses until the deadline passes. A person has to `rm` it, which the message already says for a record that won't read. Make `--clear` also remove an unvouched record, or say so in its refusal.

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 222-parked-changes (correctness)

## [2026-11-22-15] [nit] `busy_of()`'s `clean()` keeps control characters (ESC and the like), which reach `status` in the terminal; strip C0/C1 before marking

Raised by the security review of 222-parked-changes, round 1: plugins/factory/scripts/factory.py:331: `busy_of()`'s `clean()` keeps control characters (ESC and the like), which reach `status` in the terminal; strip C0/C1 before marking

Theme: robustness
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: med
Raised by: 222-parked-changes (contract)

## [2026-11-22-16] [nit] `[park] exit = 1` is accepted, which makes every ordinary red check a park; warn on 1, or document 75 as the only sensible code

Raised by the security review of 222-parked-changes, round 1: plugins/factory/scripts/factory.py:119: `[park] exit = 1` is accepted, which makes every ordinary red check a park; warn on 1, or document 75 as the only sensible code

Theme: docs
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: low
Raised by: 222-parked-changes (contract)

## [2026-11-22-17] [nit] the slot-wait test only asserts that "didn't run" appears on stderr, which proves little about the `check` message; assert the "slot" wording too

Raised by the test review of 222-parked-changes, round 1: tests/test_factory_park.py:358: the slot-wait test only asserts that "didn't run" appears on stderr, which proves little about the `check` message; assert the "slot" wording too

Theme: tests
Paths: tests/test_factory_park.py
Cost: S
Value: low
Raised by: 222-parked-changes (correctness)
