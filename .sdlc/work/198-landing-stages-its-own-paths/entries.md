# 198-landing-stages-its-own-paths — entries

Retire 2026-11-20-28: taken in by 198-landing-stages-its-own-paths

## [2026-11-20-44] [nit] the `staged_gone` comprehension still calls `_status_entries(root)` a second time, after `_stray()` has already read it.

Raised by the code review of 198-landing-stages-its-own-paths, round 1: `plugins/factory/scripts/landing.py:2923`: the `staged_gone` comprehension still calls `_status_entries(root)` a second time, after `_stray()` has already read it. `_staged()` and `_stray()` also read the index separately. One shared read would be cleaner.

Theme: refactor
Paths: plugins/factory/scripts/landing.py
Cost: S
Value: low
Raised by: 198-landing-stages-its-own-paths (correctness)

## [2026-11-20-45] [nit] the `[edit]` and `[mv]` cases both stray on `.gitignore`, and nothing separately pins that a staged rename's old path is named when only the new path is owned

Raised by the test review of 198-landing-stages-its-own-paths, round 1: tests/test_train.py:1158: the `[edit]` and `[mv]` cases both stray on `.gitignore`, and nothing separately pins that a staged rename's old path is named when only the new path is owned

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 198-landing-stages-its-own-paths (correctness)
