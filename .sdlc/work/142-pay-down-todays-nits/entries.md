# 142-pay-down-todays-nits — entries

Retire 2026-11-18-25: taken in by 142-pay-down-todays-nits
Retire 2026-11-18-28: taken in by 142-pay-down-todays-nits
Retire 2026-11-18-29: taken in by 142-pay-down-todays-nits
Retire 2026-11-18-30: taken in by 142-pay-down-todays-nits
Retire 2026-11-18-31: taken in by 142-pay-down-todays-nits
Retire 2026-11-18-34: taken in by 142-pay-down-todays-nits
Retire 2026-11-18-35: taken in by 142-pay-down-todays-nits
Retire 2026-11-18-36: taken in by 142-pay-down-todays-nits
Retire 2026-11-18-37: taken in by 142-pay-down-todays-nits

## [2026-11-18-53] [idea] Reflow AGENTS.md's remaining lines past 100 columns

Left undone by 142-pay-down-todays-nits, carried forward when it landed: `AGENTS.md` has other lines past 100 columns (12, 29, 34, the *Writes before a WAIT* paragraph at 109-110, 223, 232-233, 238, 255, 276, 314), outside 2026-11-18-25's scope.
See .sdlc/work/142-pay-down-todays-nits/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-54] [idea] Replace the "111 C1" review label in test_a_server_that_fails_on_its_own_is_started_once with the rule it pins

Left undone by 142-pay-down-todays-nits, carried forward when it landed: `tests/test_factory.py`'s `test_a_server_that_fails_on_its_own_is_started_once` docstring cites "111 C1", another review-only label no reader can resolve.
See .sdlc/work/142-pay-down-todays-nits/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-55] [idea] Wrap the supersedes sentence in reviewer-code.md and reviewer-ux.md

Left undone by 142-pay-down-todays-nits, carried forward when it landed: `plugins/factory/agents/reviewer-code.md:94` and `reviewer-ux.md:67`, the `supersedes` sentence, are single long lines.
See .sdlc/work/142-pay-down-todays-nits/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-56] [nit] the new "unverified" case asserts only `stuck == []`.

Raised by the code review of 142-pay-down-todays-nits, round 1: tests/test_factory.py:1676: the new "unverified" case asserts only `stuck == []`. Also asserting `next == "rework"` would pin the full outcome, as the neighbouring cases do.

Theme: tests
Paths: tests/test_factory.py
Cost: S
Value: low
Raised by: 142-pay-down-todays-nits (correctness)
