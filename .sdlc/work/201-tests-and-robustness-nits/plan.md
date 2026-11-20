---
id: 201
slug: tests-and-robustness-nits
kind: plan
created: 2026-11-20
updated: 2026-11-20
---

# 201 — Pay down the tests and robustness nits · plan

> How the change is built: the files it touches, the order of the work, the test each nit gets,
> and what a revert wouldn't undo. Tier 1, written because the Approach reaches across a dozen
> test files.

## Files to change

Twenty of the 29 nits were taken in by 191 too, which fixed or answered every one of them (its
plan's table names the test for each), but its landing retired only five of its 26 entries, so
they stayed open. Each was checked against the code as it stands and found done. They need no
edit, just a line in `notes.md` naming the test that settles them. Edits are needed for the nine
raised since:

- `scripts/retro.py`: `_last_experience` reads only a whole 1 to 4 back as a rating (-33);
  `_experience_text` renders its missing values through `_num()`, by name (-32).
- `tests/uv_run.py`: `UNCACHED` names uv's phrases, never a bare `offline` or `no solution
  found` (-16).
- `tests/test_adoption.py`: a script's own failure that says "offline" is its result (-16).
- `tests/test_factory_decisions.py`: the reraise test split, one case a test (-10; the nit names
  `test_factory.py`, split since).
- `tests/test_evidence_headings.py`: the blank-line rule, each side, on its own (-22).
- `tests/test_retro.py`: the insights doc's "off" (-26), the experience read-back (-33), an
  unused `tmp_path` (-34).
- `tests/test_train.py`: a path staged as kept is no deletion (-29); a moved file the resolution
  deleted is never carried, and `_neither_side()` on a gone path (-30).
- `tests/test_suite_shape.py` (new): no test takes a built-in fixture it never uses. It is the
  guard against the kind of nit -34 is, and the 30 other tests it finds today drop the argument.

Reused: `_moving()`, `_carrying()`, `_begin()`, `drive_train()`, `_folder()`, `_run()`,
`_stand_in_uv()`, `_build_report()`, `_ledger_text()`, `_felt_row()`, `_repo()`.

## Work order

1. `retro.py`'s two, test first (red: `7` and `2.5` read back as ratings).
2. `uv_run.py` (red: a script's "offline" failure skips).
3. `test_factory_decisions.py`, `test_evidence_headings.py`, `test_retro.py`'s -26 and -34.
4. `test_train.py`'s -29 and -30 (red: each against a deliberately broken copy of the guard).
5. The fixture guard (red on the tree as it is), then the 31 arguments dropped.

## Tests

| Nit | Test | Proves |
|---|---|---|
| 2026-11-20-33 | `test_a_hand_edited_rating_reads_back_as_none` | only a whole 1 to 4 is a rating |
| 2026-11-20-32 | the experience tests as they are | `—` unchanged, now by `_num()` |
| 2026-11-20-16 | `test_a_script_saying_offline_is_its_own_failure` | a script's words never skip |
| 2026-11-20-10 | `test_a_decision_reworded_with_the_same_alternatives_lands_once`, `test_a_decision_raised_again_otherwise_is_another` | each case on its own |
| 2026-11-20-22 | `test_a_blank_line_and_a_heading_end_a_command_owing_its_exit`, `test_a_heading_with_no_blank_before_it_is_output` | the blank-line rule, each side |
| 2026-11-20-26 | `test_config_reports_the_insights_doc` | off: no warning while others warn, the guide's questions alone |
| 2026-11-20-34 | `test_a_rating_with_no_line_says_so` | the argument gone |
| 2026-11-20-29 | `test_a_path_staged_as_kept_is_no_deletion` | `deleted_sides()` skips an index path |
| 2026-11-20-30 | `test_a_moved_file_the_resolution_deleted_is_not_carried` | refused, never carried; `_neither_side()` on a gone path |
| the guard | `test_no_test_takes_a_fixture_it_never_uses` | the kind of -34 can't come back |

## Rollback

Nothing outside `tests/`, `scripts/retro.py` and the change folder: `git revert` undoes all of
it.
