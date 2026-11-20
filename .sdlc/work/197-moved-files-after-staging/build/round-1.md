`resolve --continue` now accepts a modify/delete resolution after its deletion has been staged. Nit 2026-11-20-20 is closed, and the full gate passed (3477 passed, 29 skipped). Nothing is committed. `/sdlc-factory:land 194` landing without a hand step can only be shown by running that landing; this build doesn't do it.

**The cause.** 194's resolver ran `git rm` on the deleted file, despite its instructions ruling out git writes. That cleared the unmerged entries `deleted_sides()` read, so the list of files the resolver may also edit came back empty, and the file the edits were carried into was refused as a stray edit.

**Slices built** (`plan.md` written first; it covers `factory.py`, `landing.py` and two test files):
1. **Staged deletion passes (bug 2026-11-20-23).** `deleted_sides()` now reads the whole index once. Mid-rebase, it also finds a modify/delete from the commits themselves: a path no longer in the index that one side deleted since the merge base and the other changed. A file someone staged as kept is not counted. The search for the deleting commit no longer pairs renames.
2. **A staged carried file is still flagged for review.** `carried` is now any moved file whose content matches neither `HEAD` nor `REBASE_HEAD`, staged or not. The `land-resolved` marker and the `resolved` output name the modify/delete path even after it was staged.
3. **A deleted both-modified (`UU`) file is refused (nit 2026-11-20-20).** If the resolution deleted a conflicted file, or staged the deletion of a file the replayed commit keeps, `--continue` refuses unless that file is one side of a modify/delete.
4. **Evidence (nits -19, -21).** One test pins the current rule: after a read that printed output, a blank line and a `## ` heading, the section stays open. `read_evidence()`'s docstring now says when a missing `exit:` can be found past a heading.

**Tests added:**
- `test_train.py::test_a_staged_modify_delete_resolution_lands`, four cases (UD/DU × carried file edited/staged). It runs resolver, then `git rm`, then `--continue`, then the train lands. Before the fix, the edited cases were refused with the 194 message and the staged cases left `carried` empty.
- `test_train.py::test_a_deleted_both_modified_file_is_refused`, two cases (file deleted by hand, or by `git rm`). Before the fix, both were accepted.
- `test_evidence_headings.py::test_a_read_then_a_blank_heading_keeps_the_section_open`. It passed from the start, as a pin should.

**Change to `plan.md`.** `_rebasing()` moved unchanged from `landing.py` to `factory.py`, because `tests/test_modules.py` forbids factory calling landing's private helpers. Landing and the tests now call `factory._rebasing`.

**`notes.md`:** nothing left. There is no `checks.md`, since no requirement is one only a revert could break.

- UNTESTABLE: none

No decisions raised.

## Evidence

$ uv run --group dev pytest -q -n 4 tests/test_train.py -k "staged_modify_delete or deleted_both_modified" tests/test_evidence_headings.py   (before the fix)
E       AssertionError: {'state': 'refused', 'refusals': ['edited outside its conflicted files: new.txt']}
E       assert [] == ['new.txt']
E       assert (0, 'resolved') == (1, 'refused')
exit: 1

$ uv run --group dev pytest -q -n 4 tests/test_train.py -k "modify_delete or deleted_both_modified or outside_its_files or last_id_too or resolve"
15 passed in 20.15s
exit: 0

$ uv run --group dev pytest -q -n 4 tests/test_evidence_headings.py tests/test_prompts.py tests/test_modules.py tests/test_windows.py
146 passed in 1.71s
exit: 0

$ uv run --group dev ruff check plugins tests
All checks passed!
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 197
3477 passed, 29 skipped in 172.01s (0:02:52)
✔ Validation passed
✔ Validation passed
exit: 0
