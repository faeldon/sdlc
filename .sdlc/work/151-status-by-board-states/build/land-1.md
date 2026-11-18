I resolved the one conflict, which was in `scripts/board.py`, and the gate passes: 2849 tests passed, 28 skipped, exit 0.

The conflict was in two lines of the `_on_board()` docstring, which both changes had reworded. The merged text keeps both edits:

- **From 151:** `status` now "lists under Landing" instead of "lists as ready to close", matching its new column names.
- **From 149:** a stopped rebase is resolved by "its agent" instead of "its builder", since a landing's conflicts now get an agent of their own.

The rest of `board.py` merged without trouble, and 151's moves survive as built:
- `_rebasing`, `_seen`, `_touched` and `column` now live in `sdlc.py` as `rebasing_branches`, `seen_stage`, `touched_paths` and `column`.
- None of the code those moves took out of `board.py` had been changed by 149.
- 149's other rewordings in `board.py` (the landing-track comment, `step_samples`, `next_action`) are all still there.

I scanned the file afterwards: no conflict markers or calls to the moved helpers remain. I edited only `scripts/board.py` and ran no git command beyond listing the conflicted files.

## Evidence

$ git diff --name-only --diff-filter=U; grep -n '^<<<<<<<\|^=======\|^>>>>>>>\|^|||||||' scripts/board.py
scripts/board.py
180:<<<<<<< HEAD
183:=======
186:>>>>>>> 03fb711 (status groups its sections by the board's columns)

$ grep -n '^<<<<<<<\|^=======\|^>>>>>>>' scripts/board.py; grep -n '_rebasing(\|its builder\|_touched(\|_seen(' scripts/board.py
233:    touched = read("its history", lambda: sdlc.last_touched(root, rec, trunk), None)
699:    `land-verify`, its gates (`land_gates`) as `land-gate`, and its builder and resolver rows (a
(no conflict markers; the two matches above are by-design text, not the moved helpers)

$ ./check.sh > /tmp/gate151.log 2>&1; echo "exit: $?"; grep -E 'passed|failed' /tmp/gate151.log | tail -3
exit: 0
2849 passed, 28 skipped in 113.17s (0:01:53)
✔ Validation passed
✔ Validation passed
