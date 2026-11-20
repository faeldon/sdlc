VERDICT: PASS

The change does what the spec says. The gate record for this build is green, and the tests that exercise the new refusals pass.

## Notes
- **checks.md, "The review doc's Pass 1 names git state read after the step that changed it":** I expect it to pass. `.sdlc/REVIEW.md` line 55 holds the bullet `- **Git state read after the step that changed it.**`. Line 55 falls between `## Pass 1` at line 9 and `## Pass 2` at line 70, so the awk range finds it. I did not run the check.
- **R1–R5:** the four parametrised cases (edit, rm, mv, add) of `test_a_staged_path_the_replayed_commit_doesnt_own_is_refused` pass.
- **R6:** the modify/delete tests for UD and DU, the staged modify/delete resolution tests, and the `README.md` refusal test pass.
- **R7:** the non-ASCII path and settled `last-id` tests ran only as part of the gate (3540 passed). I did not run them separately.
- **R8:** `test_resolve_continue_with_no_rebase_under_way_is_refused` passes.
- **R9:** `test_resolve_continue_reads_rebase_head_once` and `test_a_deleted_both_modified_file_is_refused[git-rm]` pass.
- **Preexisting warning:** the gate record shows a warning for the missing icon on the factory plugin. It is unrelated to this change.

## Evidence
$ cat .sdlc/work/198-landing-stages-its-own-paths/build/round-1.gate.md
GATE: PASS … Command: ./check.sh … Exit: 0 … 3540 passed, 29 skipped in 165.91s … ✔ Validation passed

$ uv run --group dev pytest -q tests/test_train.py -k "owns or reads_rebase_head_once or no_rebase_under_way or outside_its_files or modify_delete or deleted_both"
12 passed, 146 deselected in 53.65s
exit: 0

$ uv run --group dev pytest -q tests/test_train.py -k "doesnt_own or reads_rebase_head_once or no_rebase_under_way"
6 passed, 152 deselected in 28.62s
exit: 0

$ git diff main --stat
.sdlc/REVIEW.md, plugins/factory/scripts/landing.py, tests/test_train.py changed (187 insertions, 22 deletions)
exit: 0

$ grep -n "^## " .sdlc/REVIEW.md
9:## Pass 1 — Correctness
70:## Pass 2 — Contract
exit: 0

$ grep -n "Git state read" .sdlc/REVIEW.md
55:- **Git state read after the step that changed it.** A landing or resolve step reads unmerged
exit: 0
