---
id: 016
slug: publish-prepare
kind: plan
created: 2026-10-25
updated: 2026-10-25
---

# 016 — A release's upload is prepared before publish's approval, and never prompts after it · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `release.prepare` in the defaults; `PREPARED_REF` (`sdlc-prepared`),
  `PREPARED_LINES`, `PREPARED_CHARS` and `_tail()` beside `AFTER_BUMP_TIMEOUT`; in `cmd_release`
  the formatted `prepare` command (a stray brace a refusal, not a traceback), a `prepare()` step
  after `after bump` (stdin closed, `after_bump`'s timeout, a tracked file it changes put back
  and refused, `restore()` on any failure, the output's tail as `prepared`) and a `note()` step
  after `tag` (never a refusal: a failure is `note_error`); `after_bump()` and publish's
  `run_command()` get a closed stdin; `cmd_publish` reports `prepared` from the tag's note.
- `skills/release/SKILL.md`: names `release.prepare`, shows it at Step 1, names it in the WAIT,
  reports `prepared` and `note_error`.
- `skills/publish/SKILL.md`: says `release.publish` runs with no terminal and stdin closed, shows
  `prepared` at Step 1 (or that nothing was prepared), and names it in the WAIT.
- `tests/test_skills.py`: `READS_CONFIG` lists `release.prepare` for release and publish.
- `tests/test_release.py`: a section on preparing the upload.
- `docs/REFERENCE.md`: the `prepare` line in `[release]`, `publish`'s non-interactive note, and the
  release and publish prose.
- `defaults/SDLC.md` and `.sdlc/SDLC.md`: the same clause naming `release.prepare`;
  `.sdlc/setup.json` re-recorded.

## Work order

1. The key, the constants and `_tail()`.
2. Closed stdin on `after_bump` and the publish command.
3. `prepare()` and `note()` in `cmd_release`.
4. `prepared` in `cmd_publish`.
5. The skills and `READS_CONFIG`.
6. The docs, `record`, `./check.sh`.

## Tests

- R1: `test_check_shows_prepare_and_runs_nothing` (the formatted command);
  `test_a_doubled_brace_reaches_the_shell_as_one`; a stray brace in any of the three commands is a
  refusal from `_host_command()`, not a traceback
  (`test_a_stray_brace_in_a_release_command_is_refused_not_raised` for `after_bump` and
  `prepare`, `test_a_stray_brace_in_the_publish_command_is_refused_not_raised`).
- R2: `test_prepare_runs_after_the_bump_and_its_output_is_noted_on_the_tag`,
  `test_prepare_runs_after_after_bump` (order, and `--check` skipping each step).
- R3: `test_a_prepare_that_changes_a_tracked_file_is_refused_and_put_back`, and
  `test_a_prepare_that_edits_a_file_the_release_changed_is_refused` (a version file it edits
  again, caught by its contents, since the bump already changed it).
- R4: `test_a_failed_prepare_puts_everything_back_and_release_runs_again`.
- R5: the noted-on-the-tag test (publish's `sdlc` note untouched),
  `test_only_the_end_of_a_long_prepare_is_kept`.
- R6: `test_publish_shows_what_release_prepared`, `test_publish_with_nothing_prepared_says_none`.
- R7: `test_a_prepare_that_asks_for_input_fails_at_once`,
  `test_a_publish_command_that_asks_for_input_fails_at_once`.
- R8: `test_prepare_stays_out_of_the_report_when_unset`, and every earlier release and publish test.
- R9: `tests/test_skills.py` (`READS_CONFIG`).
- R10: `sdlc.py drift` clean in the gate.
- R11: `test_only_publish_pushes`.
- Manual: `sdlc.py sync 016`, run through `main`'s script once `scripts/` was edited, reported
  `"ran": "the change's own code"` (015's first real check).

## Rollback

`git revert <sha>`. Not covered: a host that released with `release.prepare` keeps a note under
`refs/notes/sdlc-prepared` on its tag, harmless; `git notes --ref sdlc-prepared remove <tag>`
takes it off.
