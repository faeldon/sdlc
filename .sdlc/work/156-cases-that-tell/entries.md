# 156-cases-that-tell — entries

## [2026-11-18-99] [idea] Clear the eval workspaces left in /tmp by earlier case runs

Left undone by 156-cases-that-tell, carried forward when it landed: 26 `e-*` workspaces from earlier case runs sit in `/private/tmp` (made before runs removed their own); a one-off `run-cases --prune` or a line in CONTRIBUTING could clear them, behind the same `_workspace_of()` guard
See .sdlc/work/156-cases-that-tell/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-100] [nit] `ceiling = int((5 - spent) * 100) / 100` can lose a cent to float error (for example 4.35 becomes 4.34).

Raised by the code review of 156-cases-that-tell, round 1: scripts/sdlc.py:3877: `ceiling = int((5 - spent) * 100) / 100` can lose a cent to float error (for example 4.35 becomes 4.34). That is harmless, because it only errs low. Using `Decimal`, or `math.floor(x * 100 + 1e-9)`, would be more exact.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 156-cases-that-tell (correctness)

## [2026-11-18-101] [nit] the workspace test chmods to 0 and then restores in `finally`.

Raised by the test review of 156-cases-that-tell, round 1: tests/test_evals.py:523: the workspace test chmods to 0 and then restores in `finally`. A failure partway through could leave `outside` unreadable for pytest's tmp cleanup.

Theme: tests
Paths: tests/test_evals.py
Cost: S
Value: low
Raised by: 156-cases-that-tell (correctness)
