The build is done. `resolve --continue` now refuses any staged path that the commit being replayed (`REBASE_HEAD`) didn't touch, unless it's a conflicted file, a moved file or one of the change's landing records. The full gate run through the gate slot exited 0. Nothing is committed.

**Slices built:**
1. **The fence over staged paths (R1–R5, R7).** Two new readers sit beside `_stray()` in `landing.py`:
   - `_replayed()` lists `REBASE_HEAD`'s own paths with one `diff-tree --no-renames --name-status -z` call.
   - `_staged()` lists what the index holds that `HEAD` doesn't, with `diff --cached --name-only --no-renames -z`. With `--no-renames`, a `git mv` can't hide the path it took away.

   A shared helper, `_z_listing()`, does both reads through `subprocess.run` with `encoding="utf-8"`, never through `_git()`. The fence also refuses every staged path outside those allowed sets. The refusal's plain line now says to undo with `git checkout HEAD -- <path>`, or `git rm --cached` and delete a new file.
2. **`staged_gone` from that one listing (R6, R9).** It no longer runs `git cat-file` for each staged deletion. A staged deletion of a path `REBASE_HEAD` doesn't own now falls to the fence rather than the modify/delete check.
3. **No rebase, no read (R8).** `--continue` now refuses first when `factory._rebasing()` is false, with "no rebase under way: nothing to continue". It reads and stages nothing. Before this, that case wrote a marker, staged the records and reported "a second conflict". It also refuses if either git read fails.
4. **Docs (R10, R11).**
   - `.sdlc/REVIEW.md` Pass 1 has the bullet *Git state read after the step that changed it.*, worded as seed 2026-11-20-40 has it.
   - The docstrings of `cmd_resolve()` and `_stray()`, and the comment above the fence, state the new rule.
   - The claims in `plugins/factory/README.md`, `agents/resolver.md` and `AGENTS.md` are still true, so they're unchanged.
   - I also removed four repeated `num = ...` assignments inside `--continue`, since one is now set at the top of that branch.

**Tests added (all in `tests/test_train.py`; each failed before the fix, for the reason expected):**
- `test_a_staged_path_the_replayed_commit_doesnt_own_is_refused[edit|add|rm|mv]` (R1–R5): each case is refused, naming the path with "outside its conflicted files". No marker is written, the rebase is left under way and `README.md` is still conflicted. Once undone, the same resolution goes through and `notes.txt`, which the replayed commit staged cleanly, still lands. Before the fix all four were let through.
- `test_resolve_continue_with_no_rebase_under_way_is_refused` (R8): uses a finished rebase whose `REBASE_HEAD` is still there, plus a staged edit. Before the fix it reported "a second conflict".
- `test_resolve_continue_reads_rebase_head_once` (R9): two staged deletions; it asserts no `cat-file` and exactly one `diff-tree` on `REBASE_HEAD`. It records every `subprocess.run` call rather than `factory._git` calls, because the spec's own design routes the read past `_git()`. `plan.md` says so.

**Named runs:** the six new tests went from 6 failed to 6 passed. 34 passed across the resolve, modify/delete, counter, non-ASCII and mid-rebase tests in `test_train.py`, `test_land.py` and `test_factory_agent.py`. 204 passed in `test_defaults.py`, `test_modules.py` and `test_windows.py`. ruff check and the format check are clean.

**Files written:**
- **`plan.md`:** written from scratch, in four slices. The only departure from the spec is how the R9 test records its calls.
- **`checks.md`:** one acceptance check for R10, which finds the bullet under Pass 1.
- **`notes.md`:** none written; nothing was left over.

**Not covered (the spec's known limit):** the fence works by path. A resolver that stages different text for a path `REBASE_HEAD` owns, but that didn't conflict, still gets through. The spec leaves that for review rather than this build.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q -n 4 tests/test_train.py -k "doesnt_own or no_rebase_under_way or rebase_head_once"   (before the fix)
FAILED tests/test_train.py::test_a_staged_path_the_replayed_commit_doesnt_own_is_refused[edit]
FAILED tests/test_train.py::test_a_staged_path_the_replayed_commit_doesnt_own_is_refused[mv]
FAILED tests/test_train.py::test_a_staged_path_the_replayed_commit_doesnt_own_is_refused[rm]
FAILED tests/test_train.py::test_a_staged_path_the_replayed_commit_doesnt_own_is_refused[add]
FAILED tests/test_train.py::test_resolve_continue_reads_rebase_head_once - As...
FAILED tests/test_train.py::test_resolve_continue_with_no_rebase_under_way_is_refused
6 failed in 18.79s
exit: 1

$ uv run --group dev pytest -q -n 4 tests/test_train.py -k "doesnt_own or no_rebase_under_way or rebase_head_once"
6 passed in 8.50s
exit: 0

$ uv run --group dev pytest -q -n 6 tests/test_train.py tests/test_land.py tests/test_factory_agent.py -k "resolv or staged or modify_delete or last_id or non_ascii or rebase_head or doesnt_own or deleted_both or marker or mid_rebase or outside"
34 passed in 39.49s
exit: 0

$ uv run --group dev pytest -q -n 6 tests/test_defaults.py tests/test_modules.py tests/test_windows.py
204 passed in 1.22s
exit: 0

$ uv run --group dev ruff check plugins/factory/scripts/landing.py tests/test_train.py
All checks passed!
exit: 0

$ uv run --group dev ruff format --check plugins/factory/scripts/landing.py tests/test_train.py
2 files already formatted
exit: 0

$ sh -c "awk '/^## Pass 1/{p=1} /^## Pass 2/{p=0} p' .sdlc/REVIEW.md | grep -q '^- \*\*Git state read after the step that changed it\.\*\*'"
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 198
✔ Validation passed
exit: 0
