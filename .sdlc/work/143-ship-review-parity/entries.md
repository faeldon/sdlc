# 143-ship-review-parity — entries

## [2026-11-18-57] [idea] Tell a hand-built change how to take screenshots for ship's UI review

Left undone by 143-ship-review-parity, carried forward when it landed: Say in `ui.md`, or in `passes.ui.why` when `sdlc-factory` is enabled, how a hand-built change takes its screenshots (`factory.py shots`), once the person decides whether ship should point at a command that starts a dev server.
See .sdlc/work/143-ship-review-parity/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-58] [nit] the line says "whose own behaviour reviewer ran" and security.md and ui.md say the same of their factory reviewers.

Raised by the code review of 143-ship-review-parity, round 1: skills/ship/behaviour.md:3: the line says "whose own behaviour reviewer ran" and security.md and ui.md say the same of their factory reviewers. Only the factory case is meant, so "a factory run, whose own reviewers ran" would match `_passes_report()`'s wording.

Theme: docs
Paths: skills/ship/behaviour.md
Cost: S
Value: low
Raised by: 143-ship-review-parity (correctness)

## [2026-11-18-59] [nit] it says the pass applies when the diff touches a `review.sensitive` path.

Raised by the code review of 143-ship-review-parity, round 1: skills/ship/security.md:3: it says the pass applies when the diff touches a `review.sensitive` path. The script keys on `risk.deep`, so the sentence is only as exact as `deep` is. Say "a deep diff" to follow R2.

Theme: docs
Paths: skills/ship/security.md
Cost: S
Value: low
Raised by: 143-ship-review-parity (correctness)
