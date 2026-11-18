I resolved all five conflicted files, and none has a conflict marker left. The gate is still red on one test, `tests/test_train.py::test_a_reply_still_unreadable_after_its_mend_ejects_only_that_change`. It fails the same way on HEAD's own tree (140 stacked on 139) in a scratch copy, so the cause sits between 139 and 140, not in this resolution or in 141. My guess is that 140 now files a verdict that follows a preamble, so change 2's reply reads fine and it lands instead of being ejected. I haven't confirmed that. It isn't a conflicted file, so I left it alone; the train's gate at the tip should flag it on 140.

## What I kept from each side

The side already on the train (HEAD) is 139's landing train plus 140. The side being stacked is 141.

- **`plugins/factory/README.md`**: 139's `train` command (`--begin`, `--eject`, `--stop`) and its `resolve --onto`, with 141's wording: "a plain line over the tool's words" and "each recording its step before the commit".
- **`factory.py`**
  - **`_land_refused`**: 141 records the plain line over the raw words and returns `state: refused`. 139 still calls `_train_fail(...)` so a train ejects the change.
  - **`LAND_STEPS`**: 139's `TRAIN_RE`, `stack` and `eject`, plus 141's `checks` and `cases`.
  - **`cmd_land`**: 139's version. The train now does the rebasing, so 141's re-land code that rebased and amended in `land` had nothing left to attach to and was dropped. 141's checks-and-cases-before-the-commit rule still holds through 139's `_land_readiness`.
  - **`cmd_land_close`**: 139's train path. 141's plain line now covers every amend failure there, and the one in `_train_moved` too.
  - **`cmd_resolve`, second conflict**: 139 clears the train's `stacking` state; 141 adds its plain line.
- **`scripts/board.py`**: one step map covering both sides' steps and labels, plus 139's `LAND_STOPS`. The landing card keeps 139's `train` field ("k of n") next to 141's `early: None`.
- **`tests/test_board.py`**: `LABELS` holds both sides' entries, with 139's `STOPS`. I changed one assertion: an ejected card now goes in **Needs you**, not Close. 139 records an ejection as a stop, 141 puts a stopped landing in Needs you, and an ejected change hasn't landed.
- **`tests/test_land.py`**: I kept 139's train version of the batch test. I dropped 141's four lines asserting the stop's plain line when conflict markers are left on `resolve --continue`. Inside a train that refusal ejects the change, so the test couldn't go on to resolve and close it. Nothing else now tests that particular plain line.

## Notes for follow-up

These go in `notes.md` as unticked lines:
- [ ] The plain line for leftover conflict markers says "sdlc.py resolve N --continue finishes the rebase". That's right outside a train, but inside one the refusal ejects the change, so the advice misleads there. It needs a test outside a train too.
- [ ] `sdlc.factory_land_stop()` (used by `status`) only reads a `stop` record, not an `eject`. So the board puts an ejected change in Needs you while `status` lists no stop for it. `sdlc.py` wasn't a conflicted file, so I didn't change it.

## Evidence

$ ./check.sh
FAILED tests/test_train.py::test_a_reply_still_unreadable_after_its_mend_ejects_only_that_change
1 failed, 2604 passed, 18 skipped in 143.07s (0:02:23)
exit: 1

$ uv run --group dev pytest -q tests/test_train.py::test_a_reply_still_unreadable_after_its_mend_ejects_only_that_change   (in /tmp/head141, HEAD's tree via git archive)
FAILED tests/test_train.py::test_a_reply_still_unreadable_after_its_mend_ejects_only_that_change
1 failed in 14.88s
exit: 1

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
286 files already formatted
exit: 0

$ claude plugin validate --strict .
✔ Validation passed
exit: 0

$ grep -rn '^<<<<<<<\|^=======$\|^>>>>>>>' plugins/factory/README.md plugins/factory/scripts/factory.py scripts/board.py tests/test_board.py tests/test_land.py
(no output)
exit: 1
