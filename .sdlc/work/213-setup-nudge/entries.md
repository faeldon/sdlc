# 213-setup-nudge — entries

## [2026-11-21-16] [nit] the reflowed *Setup* paragraph leaves a short line, "same change.

Raised by the code review of 213-setup-nudge, round 1: AGENTS.md:218: the reflowed *Setup* paragraph leaves a short line, "same change. `git.attribution` has no default on", that could be rewrapped.

Theme: style
Paths: AGENTS.md
Cost: S
Value: low
Raised by: 213-setup-nudge (correctness)

## [2026-11-21-17] [nit] the R5 test never forces a `ValueError`, so half of the `except (OSError, ValueError)` is unpinned; a second mock that raises `UnicodeDecodeError` would close it

Raised by the test review of 213-setup-nudge, round 1: tests/test_setup_lifecycle.py:735: the R5 test never forces a `ValueError`, so half of the `except (OSError, ValueError)` is unpinned; a second mock that raises `UnicodeDecodeError` would close it

Theme: tests
Paths: tests/test_setup_lifecycle.py
Cost: S
Value: low
Raised by: 213-setup-nudge (correctness)
