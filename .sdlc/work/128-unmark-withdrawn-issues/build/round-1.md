I built change 128 and left it uncommitted. A full marking pass (`mark-triaged`, and close's pass) now sends an issue back to triage when core marked it and its record is gone. If a commit not yet pushed to the base branch closes that issue, the pass leaves it for the push. The gate passes: 2338 tests, 13 skipped.

**Slices** (Tier 1, three files, so no `plan.md`)
1. **Withdrawn record → unmarked** (`scripts/sdlc.py`). A full pass now calls the new `unmark_withdrawn()` after marking. It acts on an issue only when all of these hold:
   - it is still labelled `triaged`;
   - the newest comment core left on it is a mark, not a withdrawal;
   - no record in any checkout names it (`recorded_issues()`);
   - no unpushed commit closes it.
   
   It posts one comment with a `<!-- sdlc:withdrawn:<ref> -->` marker and removes the label and the parent through the tracker's `unmark()`. The issues still open to be closed come from the new `unpushed_closes()`: every message in `<remote>/<base>..<base>`, read by the tracker's `closed_by()`.
2. **Nothing unmarked on a guess.** Nothing is unmarked when there is no marks listing, the tracker has no `closed_by()`, or git can't read the commits. If git can't read them, the run says so under `failed`.
3. **Docs.** `docs/REFERENCE.md`'s intake paragraph now describes the unmarking. The `mark_issues()` docstring mentions it too.

**Tests** (`tests/test_archive.py`)
- `test_a_full_pass_unmarks_an_issue_whose_record_was_withdrawn` covers several cases:
  - An entry's `Issue:` line removed by hand gets its issue unmarked, with one comment however often the pass runs.
  - An issue a person labelled, with no comment from core, stays `dangling`.
  - An issue a person labels `triaged` again after the withdrawal is left alone.
- `test_a_full_pass_leaves_an_issue_an_unpushed_commit_closes`: close's pass and a later `mark-triaged` both leave an issue whose `Closes #50` commit isn't pushed. Once the tracking ref holds that commit, the next pass unmarks it.
- Both tests failed first for the expected reason: nothing was unmarked.

**Open question in the intent** (the unpushed range, and what happens with no tracking ref): the range is `refs/remotes/<release.remote>/<base>..<base>`, the same one `_unpushed()` uses. With no tracking ref, every commit on the base branch counts as unpushed, which is the cautious reading. I went ahead on that default, raised below.

**`notes.md`**: one unticked item. Triage's `dangling` bullet could say that an issue closed by an unpushed commit is waiting on the push.

- DECISION: [default] With no remote-tracking ref for the base branch, count every commit on the base branch as unpushed, so an issue any commit there closes is never unmarked. Options: whole base branch; unmark nothing at all. Going ahead with the whole base branch unless told otherwise: it stays cautious and still unmarks in a repo with no fetched remote.

## Evidence

$ uv run --group dev pytest -q tests/test_archive.py -k "a_full_pass"   (before the code)
FAILED tests/test_archive.py::test_a_full_pass_unmarks_an_issue_whose_record_was_withdrawn
FAILED tests/test_archive.py::test_a_full_pass_leaves_an_issue_an_unpushed_commit_closes
2 failed, 143 deselected in 47.55s
exit: 1

$ uv run --group dev pytest -q tests/test_archive.py
145 passed in 127.08s (0:02:07)
exit: 0

$ uv run --group dev pytest -q tests/test_archive.py -k "a_full_pass"
2 passed, 143 deselected in 2.21s
exit: 0

$ ./check.sh
All checks passed!
2338 passed, 13 skipped in 139.17s (0:02:19)
✔ Validation passed
✔ Validation passed
exit: 0
