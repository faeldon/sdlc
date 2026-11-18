The five conflicted files were already resolved when I started. There were no conflict markers left, and `runs/land-resolved` showed an earlier landing round (`land-1`) had handled the same files. I checked that resolution against all three changes and made no edits. The full gate passes: 2582 tests passed, 18 skipped.

To check it, I rebuilt each file's conflicts from git's three stages and compared the working tree with them.

**Kept from each side, file by file**

- **`plugins/factory/README.md`**: 139's train sentence stays (`train` with `--begin`, `--eject` and `--stop`, and `resolve --onto`). 141's wording is added to it: a stop is "a plain line over the tool's words", and `accept` and `cases` each record their step before the commit.
- **`plugins/factory/scripts/factory.py`**:
  - `LAND_STEPS` is the union of both sides: 141's `checks` and `cases` first, then 139's `stack` and `eject`, with the comment above it merged to match.
  - `_land_refused` both records the stop's plain line (141) and calls `_train_fail()` (139).
  - `cmd_land` takes 139's restructure, where `land` no longer runs `base`. That drops the old rebase branch along with 141's plain lines in it, because the code they belonged to is gone. 141's `num` is defined in the `stage: test` block that uses it.
  - Every `_close_stopped`/`_amend_record` call in `land --close`, inside or outside a train, passes 141's `_amend_plain(why, num)`. 139's new "base moved" stop keeps its own text.
  - In `cmd_resolve`, a second conflict gets 141's plain line, and a stacking change still calls 139's `_stacked_now()`.
- **`scripts/board.py`**:
  - `LAND_AT` holds 141's `checks` and `cases` at the ship position plus 139's `stack` and `eject`.
  - `LAND_LABEL` holds both sides' labels, `stacking` included.
  - 139's `LAND_STOPS = ("stop", "eject")` is kept, and the track returns both `stopped` (139) and `early: None` (141).
- **`tests/test_board.py`**: `LABELS` has both sides' entries. The one line changed outside the conflicts is the column assertion: a step in `STOPS` (139's `eject`) now expects 141's Needs you column, and every other step still expects close.
- **`tests/test_land.py`**: 139's rewrite of the end-to-end test as a train stands. 141's lines in the old version, which checked the plain line on a refused `resolve --continue`, went with the steps 139 removed. The same behaviour is still tested in `test_every_landing_stop_has_a_plain_line_over_its_raw_text` and the gate-stop test.

**Not covered by this resolution:** 141 left `factory_land_stop()` in `scripts/sdlc.py` (behind `status`) reading only `stop`. So after this merge the board treats an `eject` as a stopped landing and moves it to Needs you, but `status` does not. `sdlc.py` is outside the files I was allowed to edit, so it is unchanged here.

- DECISION: [default] Leave `status` reading only `stop` in this landing and file the `eject` case as a follow-up? Going ahead with that unless told otherwise.
  - OPTION: follow-up — the landing touches only the conflicted files; `status` and the board disagree on an ejected change until it is fixed
  - OPTION: fix it in this landing — they agree now, but it edits a file outside the conflict, which the landing forbids
  - WHY: this landing may edit only the conflicted files, and an ejected change already shows as stopped on the board.

## Evidence

$ uv run --group dev ruff check plugins/factory/scripts/factory.py scripts/board.py tests/test_board.py tests/test_land.py && uv run --group dev ruff format --check plugins/factory/scripts/factory.py scripts/board.py tests/test_board.py tests/test_land.py
All checks passed!
4 files already formatted
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_board.py tests/test_land.py tests/test_factory.py tests/test_sdlc.py
838 passed, 18 skipped in 43.48s
exit: 0

$ ./check.sh
All checks passed!
2582 passed, 18 skipped in 89.97s (0:01:29)
✔ Validation passed
exit: 0

$ grep -rn '^<<<<<<<\|^>>>>>>>' plugins/factory/README.md plugins/factory/scripts/factory.py scripts/board.py tests/test_board.py tests/test_land.py
exit: 1
