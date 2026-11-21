I fixed both open security mediums, editing only `scripts/sdlc.py` and adding two tests to `tests/test_upstream.py`. I ran no git command. Both new tests failed first for the reason each finding gave, and the full gate is now green (3725 passed, 29 skipped).

- **Medium 1: short names, and common words that are the host's own names, were never cut.**
  - Names of two characters are now cut too, but only as whole words. A short name inside a longer word (`qz` in `quiz`) is left alone, and doesn't cause the field to be left out.
  - One-character names are still never cut.
  - Common words (`origin`, `master`, the base branch and so on) are now skipped only as a branch or a config value. Where one is the host's folder, owner or user, it is cut.
  - New test: `test_upstream_cut_places_short_and_common_names_the_host_holds`.
- **Medium 2: a relative path with `..` in its middle could be sent as written.** A relative path is now kept only if it has no `..` anywhere and names a file in the plugin's own copy. `scripts/../../secret/notes.txt` now becomes `<path>`; `scripts/sdlc.py` is still kept. New test: `test_upstream_cut_never_keeps_a_relative_path_that_climbs`.

Cutting two-letter names means a host whose owner is, say, `me` will see that word turn into `<owner>` in the text. The preview shows this before anything is sent.

The security Lows are still open and recorded, not fixed here: a dotless ssh alias (`git@myalias:path`) still sends the alias name, and the host marker is matched anywhere in an issue's body, not just its first line.

## Evidence

$ uv run --group dev pytest -q tests/test_upstream.py -k "short_and_common or climbs"   (before the fix)
AssertionError: 'qz by jb, from <path>' != '<repo> by <user>, from <path>'
AssertionError: 'scripts/../../secret/notes.txt' != '<path>'
2 failed, 16 deselected in 0.54s
exit: 1

$ uv run --group dev pytest -q tests/test_upstream.py tests/test_archive.py::test_intake_flags_an_issue_from_a_host
19 passed in 5.85s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 209
All checks passed!
358 files already formatted
3725 passed, 29 skipped in 214.12s (0:03:34)
✔ Validation passed
✔ Validation passed
exit: 0
