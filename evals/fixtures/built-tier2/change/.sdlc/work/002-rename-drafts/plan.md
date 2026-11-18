---
id: 002
slug: rename-drafts
kind: plan
created: 2026-11-01
updated: 2026-11-01
---

# 002 — Rename a saved draft · plan

> Written after reading `drafts.py`.

## Files to change

- `drafts.py`: `rename()` beside `save()`.
- `test_drafts.py` (new): a test per requirement.

## Work order

1. R1: the rename and its test.
2. R2: the refusal and its test.

## Tests

- R1: `test_a_renamed_draft_keeps_its_text_under_the_new_title`.
- R2: `test_a_rename_onto_a_taken_title_changes_nothing`.

## Rollback

`git revert` undoes it; nothing is written outside the repo.
