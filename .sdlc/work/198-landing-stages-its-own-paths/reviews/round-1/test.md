VERDICT: PASS

Every requirement R1–R11 has a test that fails without it, and the gate is green. I did not run any test myself; the verdict rests on the gate's record.

## Notes

- **R1–R5:** `test_a_staged_path_the_replayed_commit_doesnt_own_is_refused[edit|add|rm|mv]` stages each stray path.
  - Each case asserts the refusal names the path and says "outside its conflicted files".
  - Each asserts no marker, the rebase still under way, and nothing staged.
  - Each then undoes the path and checks the same resolution lands. `notes.txt`, which the replayed commit staged cleanly, passes as its own.
  - In the `mv` case the new path `notes.txt` is owned by the replayed commit, so only the old-path rule can refuse it.
- **R6, R7:** these are covered by the existing tests, which the gate shows still passing.
- **R8:** `test_resolve_continue_with_no_rebase_under_way_is_refused` uses a stale `REBASE_HEAD` and a staged edit. It checks that nothing else is staged, and that `HEAD` and the marker are unchanged.
- **R9:** `test_resolve_continue_reads_rebase_head_once` records the `subprocess.run` calls during a `--continue` with two staged deletions. It asserts no `cat-file` call and exactly one `diff-tree` call on `REBASE_HEAD`, and that the resolution lands.
- **R10:** `.sdlc/REVIEW.md` holds the new bullet under Pass 1.
- **R11:** the `cmd_resolve()`, `_stray()` and fence-comment text matches the new rule, and no `cat-file` mention is left in `landing.py` or the factory README.
- **Gate record:** `build/round-1.gate.md` reports `3540 passed, 29 skipped` from `./check.sh` with exit 0, and `claude plugin validate` passed.

### checks.md

There is one check, "The review doc's Pass 1 names git state read after the step that changed it". It runs an `awk` over the Pass 1 block, then a `grep -q` for the bullet's bold lead-in. I expect it to pass now and to fail if the bullet is removed. It only reads, so it leaves the tree unchanged.

- NIT: tests/test_train.py:1158: the `[edit]` and `[mv]` cases both stray on `.gitignore`, and nothing separately pins that a staged rename's old path is named when only the new path is owned {tests S low}
