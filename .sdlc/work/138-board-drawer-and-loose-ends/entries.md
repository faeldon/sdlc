# 138-board-drawer-and-loose-ends — entries

## [2026-11-18-27] [bug] A needs-you card says "decide D1 in the factory's supervisor" without saying what D1 is or where to go

Found by the review of 138-board-drawer-and-loose-ends.
pre-existing: scripts/board.py:626: a card reads "decide D1 in the factory's supervisor". A person doesn't know what the supervisor is or where to go. This change doesn't touch that text.

Severity: low
Paths: scripts/board.py

## [2026-11-18-28] [nit] the `# fmt: skip` on the `out["dangling"]` comprehension looks unneeded, since `ruff format --check` passes without it.

Raised by the code review of 138-board-drawer-and-loose-ends, round 1: scripts/sdlc.py:7620: the `# fmt: skip` on the `out["dangling"]` comprehension looks unneeded, since `ruff format --check` passes without it. Remove it if the formatter agrees.

Theme: style
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 138-board-drawer-and-loose-ends (correctness)

## [2026-11-18-29] [nit] the Step 6 paragraph is now one 168-character line, where the rest of the file wraps near 100.

Raised by the code review of 138-board-drawer-and-loose-ends, round 2: skills/triage/SKILL.md:58: the Step 6 paragraph is now one 168-character line, where the rest of the file wraps near 100. Rewrap it at the same point as its neighbours.

Theme: style
Paths: skills/triage/SKILL.md
Cost: S
Value: low
Raised by: 138-board-drawer-and-loose-ends (correctness)

## [2026-11-18-30] [nit] the docstrings cite "138 C1" and "138 C2", which a reader can't resolve, since those labels exist only in this round's review.

Raised by the code review of 138-board-drawer-and-loose-ends, round 2: tests/test_board.py:1886-1915: the docstrings cite "138 C1" and "138 C2", which a reader can't resolve, since those labels exist only in this round's review. Say what they refer to, or cite the change's own rule.

Theme: docs
Paths: tests/test_board.py
Cost: S
Value: low
Raised by: 138-board-drawer-and-loose-ends (correctness)

## [2026-11-18-31] [nit] `test_no_build_question_for_a_refusal_or_a_spec` now checks only a Tier 1 spec refusal, since the Tier 2 spec does get a question.

Raised by the code review of 138-board-drawer-and-loose-ends, round 3: tests/test_factory.py:4437: `test_no_build_question_for_a_refusal_or_a_spec` now checks only a Tier 1 spec refusal, since the Tier 2 spec does get a question. The name still promises "a spec" with no question. Rename it to say a Tier 1 spec, or drop "spec" from the name.

Theme: tests
Paths: tests/test_factory.py
Cost: S
Value: low
Raised by: 138-board-drawer-and-loose-ends (correctness)
