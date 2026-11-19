---
id: 180
slug: workarounds-tagged
kind: plan
created: 2026-11-19
updated: 2026-11-19
---

# 180 — Workarounds are recorded, so the retrospective counts them · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/retro.py`: `_workarounds()` (new), called once by `retro()`, its result under
  `simplicity.workarounds`; helpers `_log_blocks()` (one `git log` reader, paths unescaped with
  `core.quotePath=false`), `_commands_commit()`, `_closing_subject()`, `_is_record()`,
  `_restored()`, `_overrides()`; one more
  `UNMEASURED` entry (R13). Reuses `sdlc.closed_changes()`/`dropped_changes()` (already in
  `retro()`), `bases` from `_change_rows()`, `_records_at()`, `sdlc._adoption_commit()`,
  `sdlc.CLOSE_PREFIX`, `DROP_PREFIX`, `DIR_RE`, `INBOX_SUBJECTS`, `RETRO_RE`, `ENTRY_RE`,
  `CHANGE_FOLDERS`, `INBOX`, `OLD_INBOX`, `MANIFEST`, `LAST_ID`.
- `scripts/sdlc.py`: `SETUP_SUBJECTS` (new, beside `CLOSE_PREFIX`); `TRIAGE_SUBJECT` (new, beside
  `INBOX_SUBJECTS`), which `_inbox_commit()` now uses instead of its literal `"Triage "`.
- `scripts/factory_records.py`: `ejections(show)` (new, the one parser of `EJECTIONS`, which
  `spend_rows()` now calls, its local list renamed `ejected_at` so it doesn't shadow the
  function), `LAND_ASK_RE` (new, core's own) and `land_asks(listing)` (new).
- `plugins/factory/scripts/landing.py`: `_record_ejection(folder, cause, train)` adds `train` last
  and returns a problem on `OSError` instead of raising; `_train_eject()` adds it to its output as
  `problems` (now always present, empty when none), `_train_stop()` to its own `problems`, and
  `train --run`'s loop carries an eject's `problems` on its `undos` entry, so the person sees it
  there too (`plugins/factory/skills/land/SKILL.md` says so).
- `scripts/closing.py`: docstrings of `_lead_line()` and `measure_change()` (R10).
- `.sdlc/REVIEW.md`: the doc-claim bullet under *The ways this repo's code fails* (R9).
- Docs (R12): `docs/REFERENCE.md` *Retrospectives*; `plugins/factory/README.md`'s
  `runs/ejections.jsonl` line; `skills/retro/SKILL.md`'s field list; `docs/RETRO-SCORECARD.md`'s
  *process overhead and workarounds* and S6's row.
- Tests: `tests/test_retro.py` (R1–R3, R6–R8, R13), `tests/test_train.py` (R4, R5),
  `tests/test_archive.py` (R10), `tests/test_modules.py` (R11: `RECORD_NAMES`, `LAND_ASK_RE`'s
  pin, `.ask.md` in `RECORD_FILES`), `tests/test_skills.py` (`SETUP_SUBJECTS` pinned to the
  skills).

## Work order

1. **The commit walk (R1, R2, R7's `outside`/`hand_record`/`unknown`, R8).** `SETUP_SUBJECTS`,
   `TRIAGE_SUBJECT` in `sdlc.py`; `_workarounds()` with the window's first-parent log, each closed
   change's `rev-list --first-parent <base>..<sha>`, the command subjects, outside vs record, and
   `unknown` for a change with no base. Wired into `retro()` as `simplicity`. Tests first.
2. **Restored entries (R3).** One `git log --first-parent --reverse -p --no-renames` over the
   register's paths up to the tip; each commit's net-added heading ids; an id held before and not
   held now is restored when the commit is in the window.
3. **The ejection row (R4, R5).** `train` on the row, the `OSError` a problem. Tests in
   `test_train.py`.
4. **Overrides (R6, R7's `overrides`, R11).** `factory_records.ejections()`, `land_asks()`,
   `LAND_ASK_RE`; `spend_rows()` through `ejections()`; retro counts per factory change (one with
   `decision.md`). Module pins.
5. **R10, R13, R9, R12.** Docstrings and their pin test, the `UNMEASURED` entry, the review
   bullet, the docs.

## Tests

- R1: `test_a_hand_commit_on_the_base_is_outside_the_loop` — two closes with a hand commit
  between counts 1; without it 0; a register, release, retrospective, setup and drop commit count 0.
  Also over the adoption commit's window.
- R2: `test_a_hand_commit_to_a_record_is_told_from_one_to_code`.
- R3: `test_an_entry_filed_again_after_it_was_retired_is_restored`.
- R4: `test_a_stopped_trains_rows_name_it` (`test_train.py`); 174's test unchanged.
- R5: `test_an_ejection_that_cant_be_recorded_still_ejects` (`test_train.py`): `ejections.jsonl`
  made a directory, so the append raises `OSError`.
- R6: `test_overrides_are_read_from_each_factory_changes_commit`.
- R7: `test_with_no_factory_change_the_overrides_are_null`,
  `test_a_change_with_no_start_leaves_its_commits_unknown`.
- R8: each new retro test checks `git status` and `HEAD` unchanged; the existing read-only tests.
- R9: `tests/test_defaults.py` as it is.
- R10: `test_measures_errors_never_become_a_trailer` (`test_archive.py`).
- R11: `tests/test_modules.py` (`RECORD_NAMES`), `test_land_ask_re_reads_the_factorys_path`.
- R12: no test; the review greps the docs.
- R13: `test_counts_tiers_impacts_and_what_history_cannot_measure` extended.
- R9, R12: `checks.md`, two acceptance checks (lines added to docs only a revert removes).
- `SETUP_SUBJECTS`: `test_setup_subjects_are_the_skills_own` (`test_skills.py`).

## Rollback

`git revert` undoes all of it. Rows already written to a change's `runs/ejections.jsonl` with a
`train` key stay in history; 174's reader ignores the key, so nothing needs undoing.
