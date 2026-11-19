# 167-board-knows-its-repo — entries

## [2026-11-19-11] [nit] `_bare_repo` creates a repo with no `user.name` or `user.email`.

Raised by the test review of 167-board-knows-its-repo, round 1: tests/test_board.py:660: `_bare_repo` creates a repo with no `user.name` or `user.email`. It passes on this machine, but may fail on a clean CI box. Reuse the `repo` fixture's git config if it sets one.

Theme: tests
Paths: tests/test_board.py
Cost: S
Value: low
Raised by: 167-board-knows-its-repo (correctness)
