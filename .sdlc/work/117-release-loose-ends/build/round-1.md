The release fixes are built and the full gate passes: `./check.sh` exits 0 with 2209 passed and 9 skipped. Everything is uncommitted in the worktree for `/sdlc:ship`.

**What was built** (one slice at a time, each test seen failing first):
1. **`__version__` lines (R5).** `VERSION_RE` now also reads `__version__ = "x"`, so reading and writing versions needed no other change. `my__version__` and `target-version` still don't count. Test: `test_python_s_dunder_version_is_a_version_line`.
2. **Missing-tag hint (R6).** When no tag exists for the current version, the hint now names the commit that first added `.sdlc/config.toml` if that came after the last version change. If the version was bumped after adoption, it still names the bump. Tests: `test_a_missing_tag_points_at_adoption_when_it_came_after_the_version` and `test_a_version_bump_after_adoption_is_still_the_hint`. The existing missing-tag test still passes.
3. **Changelog marker and template (R1–R4).**
   - A line `<!-- sdlc:releases -->` in the changelog now marks where each release's section goes; everything above it is kept byte for byte.
   - Without the marker, the output is byte-identical to today's. That includes a CRLF quirk: today's code leaves `\n\r\n` before the older section, and the test pins it rather than fixing it.
   - The section comes from a new `templates/changelog.md` that a host can override. An override missing `{{notes}}` shows up in drift as breaking.
   - Tests: `test_a_marker_places_the_release_after_it`, `test_without_a_marker_the_changelog_is_written_as_before` (titled, untitled, no title, empty, CRLF), `test_a_host_changelog_template_shapes_the_section`, `test_a_brace_in_a_note_is_never_a_format_error` and `test_a_changelog_template_without_notes_is_breaking`.
   - As you decided (open question B), AGENTS.md now names `templates/changelog.md` as the second exception to the doc-shape rule, and `tests/test_defaults.py` has the matching entry.
4. **Publish pushes its record (R7, R9, R10).**
   - After the publish command succeeds, publish pushes `refs/notes/sdlc` through the existing push function, never forced.
   - If the remote refuses that push, publish still exits 0 and reports `notes_push_failed`.
   - `publish --check` lists `push notes` in `will_run` whenever it lists the command.
   - With no publish command, no notes move.
   - Tests: `test_publish_pushes_the_published_note`, `test_a_refused_notes_push_does_not_fail_publish` and `test_publish_without_a_command_moves_no_notes`.
5. **A second clone skips the upload (R8).**
   - After the yes, and only when there is a command, publish fetches the remote's notes into `refs/notes/sdlc-remote` and merges them into its own.
   - The merge creates the local notes ref when there isn't one; I checked that in a scratch repo before writing the plan.
   - Tests: `test_a_second_clone_skips_the_upload_another_made`, where the upload counter stays at one, and `test_a_second_clone_s_own_notes_survive_the_fetch`.
6. **Docs and skill (R11, R12).**
   - `docs/REFERENCE.md` now covers version files, the changelog marker, publishing, the `changelog.md` template and the config comment. For the dry run (`--dry-run`) it suggests `git lfs push --dry-run origin {tag}`.
   - The publish skill names `push notes` and explains `notes_push_failed` and `notes_fetch_failed`. I also corrected its *Out of scope* line, which said publish pushes nothing but `main` and the tag. No new commands or `Bash(...)` rules were added.
   - Test: `test_reference_names_the_changelog_marker_and_the_notes_push`.

**Existing tests I changed:**
- Three publish tests in `tests/test_release.py` now expect `done` to end with `push notes`.
- One `will_run` assertion in `tests/test_push.py` gains `push notes`, as R7 requires.
- `test_only_the_named_steps_push` itself is unchanged, but it caught a false positive: my docstring for the new fetch function contained the text `_push(`. I reworded the docstring rather than the test.

**Changes to `plan.md`:**
- `record` wasn't run because drift reported nothing after the template was added.
- It names the two extra tests and the wider skill edits.

**Not tested:** the path where the notes fetch fails (`notes_fetch_failed`). It is hard to fake against a bare repo on disk. The code is short and only adds a report field. Nothing was added to `notes.md`.

No decisions raised: both open questions were already settled in `intent.md`.

## Evidence

$ uv run --group dev pytest -q tests/test_release.py -k dunder   (before the code)
FAILED tests/test_release.py::test_python_s_dunder_version_is_a_version_line
exit: 1

$ uv run --group dev pytest -q tests/test_release.py -k "missing_tag or bump_after"   (before the code)
1 failed, 2 passed, 71 deselected
exit: 1

$ uv run --group dev pytest -q tests/test_release.py -k "changelog or marker or brace_in_a_note"   (before the code)
AttributeError: module 'sdlc_release' has no attribute 'changelog_section'
exit: 1

$ uv run --group dev pytest -q tests/test_release.py -k "note or second_clone"   (before the code)
4 failed, 5 passed, 79 deselected in 3.51s
exit: 1

$ uv run --group dev pytest -q tests/test_release.py -k reference   (before the docs)
AssertionError: <!-- sdlc:releases -->
exit: 1

$ uv run --quiet --script scripts/sdlc.py drift
breaking [] refresh [] report []
exit: 0

$ ./check.sh
All checks passed!
249 files already formatted
2209 passed, 9 skipped in 163.38s (0:02:43)
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_release.py tests/test_push.py tests/test_skills.py::test_only_the_named_steps_push
109 passed in 53.42s
exit: 0
