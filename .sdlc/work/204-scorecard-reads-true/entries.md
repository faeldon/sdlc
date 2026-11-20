# 204-scorecard-reads-true — entries

Retire 2026-11-20-25: taken in by 204-scorecard-reads-true

## [2026-11-20-56] [idea] Surface key scan follows calls only, to separate always-read keys from branch-read keys

Left undone by 204-scorecard-reads-true, carried forward when it landed: The scan's reach could follow only calls, not every mention of a name, if the surface's key share should separate keys a command reads on every run from keys it reads on one branch.
See .sdlc/work/204-scorecard-reads-true/notes.md in its commit.
Raised 2026-11-20.

## [2026-11-20-57] [nit] the line `restored \`no register entry added in the window\`.

Raised by the code review of 204-scorecard-reads-true, round 1: docs/REFERENCE.md:1344: the line `restored \`no register entry added in the window\`. A greyed block's note…` is now over-long after the reflow; rewrap it

Theme: docs
Paths: docs/REFERENCE.md
Cost: S
Value: low
Raised by: 204-scorecard-reads-true (correctness)
