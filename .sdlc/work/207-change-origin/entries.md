# 207-change-origin — entries

## [2026-11-21-3] [nit] the register paragraph now has a line well over 100 characters, because "Each line's command is `/sdlc:intent <id>`." was glued onto the end of the new clause.

Raised by the code review of 207-change-origin, round 1: docs/REFERENCE.md:508: the register paragraph now has a line well over 100 characters, because "Each line's command is `/sdlc:intent <id>`." was glued onto the end of the new clause. Rewrap it

Theme: style
Paths: docs/REFERENCE.md
Cost: S
Value: low
Raised by: 207-change-origin (correctness)

## [2026-11-21-4] [nit] the two lines edited for `origin:` run past the file's wrapping width.

Raised by the code review of 207-change-origin, round 1: skills/intent/batch.md:34: the two lines edited for `origin:` run past the file's wrapping width. Rewrap them

Theme: style
Paths: skills/intent/batch.md
Cost: S
Value: low
Raised by: 207-change-origin (correctness)

## [2026-11-21-5] [nit] `origin_trailer()` catches every `Exception`, not just a git or read failure, so a coding error there would make origins quietly unknown on every close instead of failing a test; `fix_trailers()` does the same

Raised by the security review of 207-change-origin, round 1: scripts/closing.py:558: `origin_trailer()` catches every `Exception`, not just a git or read failure, so a coding error there would make origins quietly unknown on every close instead of failing a test; `fix_trailers()` does the same

Theme: robustness
Paths: scripts/closing.py
Cost: S
Value: low
Raised by: 207-change-origin (contract)

## [2026-11-21-6] [nit] `test_idea_and_bug_offer_an_origin_line` only asserts that `Origin: self` is absent from the skill text.

Raised by the test review of 207-change-origin, round 1: tests/test_skills.py: `test_idea_and_bug_offer_an_origin_line` only asserts that `Origin: self` is absent from the skill text. It would not catch the skills telling the person to write `self` in other words

Theme: tests
Paths: tests/test_skills.py
Cost: S
Value: low
Raised by: 207-change-origin (correctness)
