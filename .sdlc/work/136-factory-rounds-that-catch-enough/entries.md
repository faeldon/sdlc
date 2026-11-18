# 136-factory-rounds-that-catch-enough — entries

## [2026-11-18-33] [idea] Show an early stop's reason (stuck/untestable) on the board's card and in runs/stopped.md

Left undone by 136-factory-rounds-that-catch-enough, carried forward when it landed: The board's step track and `runs/stopped.md` don't show `stuck` or `untestable`: an early stop reads on the board as a plain `approve`. Worth a line on the card once the retro's counts show how often it happens.
See .sdlc/work/136-factory-rounds-that-catch-enough/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-34] [nit] this line still describes `exhausted` only as "rounds ran out".

Raised by the code review of 136-factory-rounds-that-catch-enough, round 1: plugins/factory/skills/build/SKILL.md:416: this line still describes `exhausted` only as "rounds ran out". It is now also true for a `stuck` or `untestable` stop. Add a clause saying the approver is told which.

Theme: docs
Paths: plugins/factory/skills/build/SKILL.md
Cost: S
Value: med
Raised by: 136-factory-rounds-that-catch-enough (correctness)

## [2026-11-18-35] [nit] its diff is 5 lines, against 8 for the other reviewers.

Raised by the code review of 136-factory-rounds-that-catch-enough, round 1: plugins/factory/agents/reviewer-ux.md: its diff is 5 lines, against 8 for the other reviewers. Check that the word-for-word re-raise sentence reads the same there.

Theme: docs
Paths: plugins/factory/agents/reviewer-ux.md
Cost: S
Value: low
Raised by: 136-factory-rounds-that-catch-enough (correctness)

## [2026-11-18-36] [nit] R6's README table of changes 124, 125, 129 and 131 has no test.

Raised by the test review of 136-factory-rounds-that-catch-enough, round 1: tests/test_factory.py:1676: R6's README table of changes 124, 125, 129 and 131 has no test. It cannot be checked mechanically, so a person should confirm it against each change's `Close` commit.

Theme: tests
Paths: tests/test_factory.py
Cost: S
Value: low
Raised by: 136-factory-rounds-that-catch-enough (correctness)

## [2026-11-18-37] [nit] the R3 test has no case where round N-1 has no `verified.md`, which the code handles.

Raised by the test review of 136-factory-rounds-that-catch-enough, round 1: tests/test_factory.py:1358: the R3 test has no case where round N-1 has no `verified.md`, which the code handles. A one-line fixture would pin that branch.

Theme: tests
Paths: tests/test_factory.py
Cost: S
Value: low
Raised by: 136-factory-rounds-that-catch-enough (correctness)
