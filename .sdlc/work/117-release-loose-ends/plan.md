---
id: 117
slug: release-loose-ends
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 117 — Release keeps a host's changelog and version lines, and publish's note leaves the machine · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`:
  - `VERSION_RE` also reads `__version__`. Its groups are unchanged, so `read_versions()` and `write_version()` are untouched.
  - `CHANGELOG_MARKER`, a new `changelog_section()` that renders through `template_path()`, and `with_changelog(text, section)` with the marker branch. `cmd_release`'s `changelog()` step calls both.
  - `DOC_TEMPLATES` gains `changelog.md`, and `TEMPLATE_READS["changelog.md"]` gets the placeholders `{{version}}` and `{{notes}}`.
  - A new `_adoption_commit(home)`. `unreleased()`'s missing-tag hint picks the later of it and the last version commit, using `git merge-base --is-ancestor` through `_git_err`.
  - A new `_fetch_notes(home, remote)`, called only by `cmd_publish`: `ls-remote` first, then a fetch without `+` into `refs/notes/sdlc-remote`, then `git notes --ref sdlc merge -s cat_sort_uniq`. It runs with `GIT_TERMINAL_PROMPT=0` and stdin closed.
  - `cmd_publish` gets the fetch after the refusals (only with a command, and not under `--check`), and a notes push after the step loop, through `_push()`, whose failure is `notes_push_failed` and not exit 1. `--check` adds `push notes` to `will_run` when `publish command` is there.
- `templates/changelog.md` (new): `## {{version}} — {{date}}`, a blank line, then `{{notes}}`. It is rendered verbatim.
- `tests/test_defaults.py`: an `EXCEPTIONS` entry for `templates/changelog.md`.
- `AGENTS.md`: the "one shape" bullet names both verbatim templates. The person approved this (intent, open question B).
- `.sdlc/setup.json`: unchanged. `sdlc.py drift` reported nothing after the template was added, so `record` was not run (the spec runs it only if drift lists the template).
- `tests/test_release.py`: the new tests R1–R9 and R11, plus updates to the existing publish tests whose `done` now ends with `push notes`.
- `tests/test_push.py`: `test_a_publish_command_release_left_is_named_with_the_push`'s `will_run` gains `push notes`.
- `docs/REFERENCE.md`:
  - *Releases*: the marker, the template, `__version__`, the hint, the notes push and fetch, `--notes-from-tag`, a `prepare` dry run, and tags outside the pattern.
  - *Templates*: `changelog.md`.
  - The config example's `changelog` comment.
- `skills/publish/SKILL.md`: Step 0's `will_run` list and Step 3 name `push notes`, Step 4 says what `notes_push_failed` and `notes_fetch_failed` mean, and *Out of scope* now allows pushing the publish record. There are no new commands.

## Work order

1. **Version line (R5).** Test first, then the regex change.
2. **Missing-tag hint (R6).** Two tests, then `_adoption_commit` and the hint.
3. **Changelog template + marker (R1–R4).** Tests for: the unchanged bytes with no marker (titled, untitled, empty and CRLF), the marker, a host template, and drift's `breaking`. Then the template file, `changelog_section`, the `with_changelog` signature and marker, the registry entries, `EXCEPTIONS`, AGENTS.md and `record`.
4. **Notes push (R7, R9).** Tests, then the post-loop notes step and the `--check` `will_run`. Update the existing publish tests' `done`.
5. **Second clone (R8, R10).** Test, then `_fetch_notes` and its call before the steps.
6. **Docs and skill (R11, R12).** The grep test, then REFERENCE.md and the publish skill.
7. Run the gate.

## Tests

- R1 `test_a_marker_places_the_release_after_it`
- R2 `test_without_a_marker_the_changelog_is_written_as_before`, plus the existing notes/changelog test
- R3 `test_a_host_changelog_template_shapes_the_section`, `test_a_brace_in_a_note_is_never_a_format_error`
- R4 `test_a_changelog_template_without_notes_is_breaking`, plus the existing readiness/template-list tests in `tests/test_defaults.py`
- R5 `test_python_s_dunder_version_is_a_version_line`, plus the existing `target-version` assertion
- R6 `test_a_missing_tag_points_at_adoption_when_it_came_after_the_version`, `test_a_version_bump_after_adoption_is_still_the_hint`, plus the existing missing-tag test
- R7 `test_publish_pushes_the_published_note`, `test_a_refused_notes_push_does_not_fail_publish`
- R8 `test_a_second_clone_skips_the_upload_another_made`, `test_a_second_clone_s_own_notes_survive_the_fetch` (the `cat_sort_uniq` merge keeps local notes and pushes the merge back)
- R9 `test_publish_without_a_command_moves_no_notes`
- R10 `tests/test_skills.py::test_only_the_named_steps_push`, unchanged
- R11 `test_reference_names_the_changelog_marker_and_the_notes_push`
- R12 `tests/test_skills.py`, unchanged

## Rollback

`git revert` covers the code, the template and the docs. It does not cover notes already pushed to a host's remote: `refs/notes/sdlc` there holds only the word `published` per tag, and nothing reads it once reverted. A host can delete it with `git push <remote> :refs/notes/sdlc`. The local mirror `refs/notes/sdlc-remote` is removed with `git update-ref -d refs/notes/sdlc-remote`.
