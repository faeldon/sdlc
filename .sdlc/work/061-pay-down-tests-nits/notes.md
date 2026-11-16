# 061 — Pay down the tests nits · notes

## Each test shown to fail on what it guards

Each mutation was made in the worktree, the one test run, and the file restored from a copy
(`git diff` empty after).

- **2026-10-24-7** (`test_status_is_unchanged_without_a_registry`): no mutation needed; its third
  half asserts a registry holding a shim changes status, so the comparison it makes can fail.
- **2026-10-25-22** (`test_a_dropped_change_records_no_fixes`): `_drop_record` made to append
  `fix_trailers()` to the `Drop` message → failed.
- **2026-11-04-1** (`test_it_refuses_before_writing_anything[_review_too]`): `.sdlc/REVIEW.md`
  added to `cmd_retro_commit`'s allowed set → failed.
- **2026-10-26-14** (`test_readiness_has_no_inbox_item`): an `inbox` item added to
  `cmd_readiness` → failed.
- **2026-11-04-12** (`test_a_write_mode_open_without_newline_is_caught`): proves itself on a
  synthetic source: `open(p, "w")`, `p.open("a")`, `open(p, mode="x")` caught; `newline=`, `rb`,
  a read and `os.open` passed over. The scripts hold no write-mode `open` today.
- **2026-11-04-14** (`test_the_factory_s_streams_are_sdlc_s`): the factory's `_utf8_streams`
  narrowed to stdout → failed. The copies were identical, so no script changed.
- **2026-11-13-2** (`test_a_skill_s_side_files_are_named_by_it_and_hold_no_gate`): ship's
  `cases.md` moved away, leaving `SKILL.md`'s bare pointer → "names ['cases.md'], which no file
  is". A rename is already caught by the older half ("never names").

## Departures from the plan

- **2026-10-25-22's test lives in `tests/test_archive.py`**, not `tests/test_bugs.py`: it needs the
  close and drop harness and the fake `gh` there. The source-grep test in `test_bugs.py` is gone.
- **`WRITTEN_ELSEWHERE` holds `decision.md` and `decisions.md`**: the factory's agents write them
  into a change's folder, and no file in the repo carries either name.
