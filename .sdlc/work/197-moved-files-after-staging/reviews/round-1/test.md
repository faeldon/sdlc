VERDICT: PASS

## Notes

Requirements are mapped from the intent's Outcome list.
- **Staged deletion passes, in landing order (bug -23, "lands without a hand step"):** `tests/test_train.py::test_a_staged_modify_delete_resolution_lands` runs the resolver, then `git rm --cached`, then `--continue`, then the rest of the train. It asserts no unmerged entry is left, that `carried == ["new.txt"]`, that the deletion stands at `HEAD`, that the marker reads `old.txt, new.txt`, and that both changes land. It is parametrized over UD/DU and edited/staged carried file. It fails without `deleted_sides()` reading the commits, because `--continue` would refuse `new.txt` as a stray edit.
- **Staged carried file is still named:** the `staged` parameter covers it. It fails under the old `xy[1] != " "` check, because the file's status is then `M ` and not `MM`.
- **Nit -20, a deleted `UU` file is refused:** `test_a_deleted_both_modified_file_is_refused` covers it. It tries both an unlinked file and `git rm -f`, and asserts the refusal names `README.md` and "modify/delete", that no marker is written, and that the rebase is left under way.
- **Nit -19, evidence:** `test_a_read_then_a_blank_heading_keeps_the_section_open` pins the behaviour. The plan chose to document it and pin it, not change the rule, and the docstring was updated for nit -21.
- **Existing tests:** the 196 modify/delete tests are unchanged, and the `_rebasing` move is covered by the updated reference in `test_a_resolution_outside_its_files_is_refused`.
- **Gate:** the record `build/round-1.gate.md` shows `GATE: PASS`, `./check.sh` exit 0, "3477 passed, 29 skipped in 169.23s". The new train tests are marked `@needs_uv` and skip where uv is absent, as the neighbouring tests do. I did not run any tests myself.
- **Checks:** there is no `checks.md`, and none is needed.

- NIT: tests/test_train.py: nothing pins the guard in `deleted_sides()` that a path staged as kept (present in the index, changed on one side and deleted on the other) is not treated as a deletion. Only the gone-from-index direction is tested. {tests S med}
- NIT: tests/test_train.py: `_neither_side()` returns True when git can't hash a moved file, so a moved file that is gone from the tree counts as `carried`. No test covers that case. {tests S low}
