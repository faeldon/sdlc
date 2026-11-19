# 173-style-paydown — entries

Retire 2026-11-18-75: taken in by 173-style-paydown
Retire 2026-11-18-76: taken in by 173-style-paydown
Retire 2026-11-18-77: taken in by 173-style-paydown
Retire 2026-11-18-78: taken in by 173-style-paydown
Retire 2026-11-18-83: taken in by 173-style-paydown
Retire 2026-11-18-96: taken in by 173-style-paydown
Retire 2026-11-18-108: taken in by 173-style-paydown
Retire 2026-11-19-10: taken in by 173-style-paydown
Retire 2026-11-19-5: taken in by 173-style-paydown

## [2026-11-19-27] [idea] Rewrap the remaining factory agents' prose lines past 100 columns

Left undone by 173-style-paydown, carried forward when it landed: The other factory agents (`approver.md`, `builder.md`, `resolver.md`, `reviewer-behaviour.md`, `reviewer-security.md`, `reviewer-test.md`, `reviewer-ui.md`, `spec-writer.md`, `verifier.md`) keep prose lines past 100 columns; no entry named them, so they stayed out of this change.
See .sdlc/work/173-style-paydown/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-28] [nit] the round-file sentence ("and `factory.py` writes it to `.sdlc/work/NNN-slug/reviews/round-N/test.md`…") is 105 columns, the same shape -81 fixed in `reviewer-code.md` and `reviewer-ux.md`; its "Under a decision's line" paragraph is probably the same; the change names only the first two files, so this is out of scope here

Raised by the test review of 173-style-paydown, round 1: plugins/factory/agents/reviewer-test.md:13: the round-file sentence ("and `factory.py` writes it to `.sdlc/work/NNN-slug/reviews/round-N/test.md`…") is 105 columns, the same shape -81 fixed in `reviewer-code.md` and `reviewer-ux.md`; its "Under a decision's line" paragraph is probably the same; the change names only the first two files, so this is out of scope here

Theme: docs
Paths: plugins/factory/agents/reviewer-test.md
Cost: S
Value: low
Raised by: 173-style-paydown (correctness)

## [2026-11-19-29] [nit] the first check covers only the seven named files, so a rewrap that regressed another agent file would not be caught; fine for this scope

Raised by the test review of 173-style-paydown, round 1: .sdlc/work/173-style-paydown/checks.md: the first check covers only the seven named files, so a rewrap that regressed another agent file would not be caught; fine for this scope

Theme: tests
Paths: .sdlc/work/173-style-paydown/checks.md
Cost: S
Value: low
Raised by: 173-style-paydown (correctness)
