I couldn't finish the landing. The conflict in `tests/test_train.py` is resolved, but the gate is still red. One of the two failures needs an edit to `factory.py`, which this landing doesn't allow me to touch.

**The conflict.** It was a single block where two changes each added tests after `test_a_train_stops_past_land_moves`. I kept both sides in full:
- **From 145:** `_waits()` and `test_a_waiting_change_records_what_it_waits_on` (145 R22) stay as they were, except for one renamed call. That test called `_drive(root, capsys, …)`, a helper 147 moved to `tests/train_driver.py` as `drive_train(factory, root, capsys, …)`. I changed its three calls to the new name; the arguments are the same.
- **From 147:** everything on its side stays as written, from `test_every_ejection_names_its_cause` (R16) through `test_a_killed_train_run_resumes` (R8).
- **From 144 and 146:** neither touched this part of the file, and their changes elsewhere are untouched.

No conflict markers remain, and ruff format and ruff check are clean.

**Why the gate is red.** The gate ran 2,828 tests: 2,826 passed, 2 failed, 28 were skipped.

1. **`test_a_resolution_leaves_the_worktree_clean` (147 R14)** fails because the worktree is left holding an untracked `.sdlc/work/002-second/runs/land-times.jsonl`. 145 added that file (`LAND_TIMES`, a new row each time a change's landing step changes). 147's `resolve --continue` stages only `RESOLVE_RECORDS`, which predates 145 and doesn't include it. The two changes are each fine alone but break together. The fix is to add `LAND_TIMES` to `RESOLVE_RECORDS` in `plugins/factory/scripts/factory.py`. Weakening the test would undo what 147 was built to do, so I left it as written.
2. **`test_nothing_in_the_repo_is_forbidden`** flags 144's own record, `.sdlc/work/144-factory-records-and-models/entries.md:9`. That nit cites folder-numbered paths (`work/<008>…`), which the test forbids. It is 144's text, not mine to edit. The test reports 12 offending lines, but its output only names that first one; I didn't trace the other 11.

- DECISION: [blocking] Let the landing add `LAND_TIMES` to `RESOLVE_RECORDS` in `factory.py`, a file outside the conflict? Recommend yes.
  - OPTION: allow the one-line `factory.py` edit — R14 (clean worktree after a resolution) holds alongside 145's land times; it reaches past the conflicted files
  - OPTION: eject 147 and fix it in its own rework round — the landing stays within its rules; 147 waits a round
  - WHY: it's a one-line fix where 145 and 147 meet, and 147's test already proves it
- DECISION: [blocking] How should 144's `entries.md` nit stop citing a folder-numbered path (`work/<008>…`)? Recommend rewording it with a neutral slug.
  - OPTION: reword the nit in 144's folder — the rule in `tests/test_nothing_local.py` holds; it edits another change's record
  - OPTION: eject 144 to fix it there — each change fixes its own record; the train gets shorter
  - WHY: the repo's rule is that nothing may cite a change by folder number

## Evidence

$ uv run --group dev ruff format tests/test_train.py && uv run --group dev ruff check tests/test_train.py
1 file left unchanged
All checks passed!
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_train.py
FAILED tests/test_train.py::test_a_resolution_leaves_the_worktree_clean - Ass...
1 failed, 42 passed in 49.51s
exit: 1

$ uv run --group dev pytest -q tests/test_train.py::test_a_resolution_leaves_the_worktree_clean
E         + ?? .sdlc/work/002-second/runs/land-times.jsonl
exit: 1

$ git log --oneline -S'LAND_TIMES' -- plugins/factory/scripts/factory.py
b1db779 An escalation the person has dealt with clears without a rebuild

$ ./check.sh
FAILED tests/test_nothing_local.py::test_nothing_in_the_repo_is_forbidden - A...
FAILED tests/test_train.py::test_a_resolution_leaves_the_worktree_clean - Ass...
2 failed, 2826 passed, 28 skipped in 124.10s (0:02:04)
exit: 1

$ uv run --group dev pytest -q tests/test_nothing_local.py
E         Left contains 12 more items, first extra item: '.sdlc/work/144-factory-records-and-models/entries.md:9: ## [2026-11-18-62] [nit] `work/<008>*x` is rewritten to `work/008-slug*x`, …'
exit: 1
