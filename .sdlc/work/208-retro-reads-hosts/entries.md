# 208-retro-reads-hosts — entries

## [2026-11-21-13] [nit] R3 says a listed path under this repo's `.claude/worktrees/` is skipped and counted as `own`.

Raised by the test review of 208-retro-reads-hosts, round 1: tests/test_retro_hosts.py:329: R3 says a listed path under this repo's `.claude/worktrees/` is skipped and counted as `own`. Only the main checkout is listed in the fixtures, so the worktree case is never exercised. Add a worktree path to `_listed`.

Theme: tests
Paths: tests/test_retro_hosts.py
Cost: S
Value: med
Raised by: 208-retro-reads-hosts (correctness)

## [2026-11-21-14] [nit] the `!` exclusion is only shown against a path that doesn't exist, so it would pass even if an excluded host were still read.

Raised by the test review of 208-retro-reads-hosts, round 1: tests/test_retro_hosts.py:325: the `!` exclusion is only shown against a path that doesn't exist, so it would pass even if an excluded host were still read. Exclude a real fixture host and assert it is absent from `read`.

Theme: tests
Paths: tests/test_retro_hosts.py
Cost: S
Value: med
Raised by: 208-retro-reads-hosts (correctness)

## [2026-11-21-15] [nit] R12 says no host figure enters the indicators the next retro reads back.

Raised by the test review of 208-retro-reads-hosts, round 1: tests/test_retro_hosts.py:426: R12 says no host figure enters the indicators the next retro reads back. The test compares `retro`'s JSON with and without a list, but doesn't compare the report's indicators block.

Theme: tests
Paths: tests/test_retro_hosts.py
Cost: S
Value: low
Raised by: 208-retro-reads-hosts (correctness)
