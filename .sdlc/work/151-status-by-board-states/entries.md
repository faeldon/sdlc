# 151-status-by-board-states — entries

## [2026-11-18-86] [nit] `a["ready"]` now adds `held_by_rebase(home)`.

Raised by the code review of 151-status-by-board-states, round 1: scripts/sdlc.py:10620: `a["ready"]` now adds `held_by_rebase(home)`. That function calls `_change_trees` and `worktrees`, which `rebasing_branches` also calls, so `status` walks the worktree list twice. It's cheap, but `held_by_rebase` could take the branches as an argument.

Theme: refactor
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 151-status-by-board-states (correctness)

## [2026-11-18-87] [nit] `_by_state` falls back to `BY_STAGE` for a record with no `column`, and silently drops a stage `column()` would place elsewhere, such as `test`.

Raised by the code review of 151-status-by-board-states, round 1: scripts/sdlc.py:10010: `_by_state` falls back to `BY_STAGE` for a record with no `column`, and silently drops a stage `column()` would place elsewhere, such as `test`. Nothing reads such a record today.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 151-status-by-board-states (correctness)
