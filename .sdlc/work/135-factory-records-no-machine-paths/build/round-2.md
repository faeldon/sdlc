I fixed the one kept change: a read naming a home path is a read again, so it no longer owes an `exit:` line or costs a mend. The full gate passes: 2408 passed, 13 skipped.

- KEPT code C1 (`is_read()` taking `<home>` as a redirect): **fixed.** Before splitting the command into tokens, `is_read()` now swaps `<home>` for `HOME` and `<path-to-clone>` for `CLONE`, as the reviewer suggested. The `<path-to-clone>` mark already had this problem before this change; the swap fixes it too.

The new test is `test_a_read_naming_a_mark_is_still_a_read`, marked `portable`. For each mark it checks three things:
- `ls <mark>/.nvm/bin` counts as a read.
- A reply whose evidence runs that command and prints a line, with no `exit:`, passes `read_evidence()` with nothing reported.
- A real redirect next to a mark is still not a read, both `cat <mark>/a > <mark>/b` and `cat <mark>/a >out`.

It failed before the fix, on `is_read("ls <home>/.nvm/bin")` returning False.

`plan.md` now lists the `is_read()` change and the new test. I also corrected two places that had drifted from what was built: it said two new tests where there are three, and slice 2 said "a review" where the test files a builder report.

No decisions raised this round, and nothing new in `notes.md`.

## Evidence

$ uv run --group dev pytest -q tests/test_factory.py -k read_naming_a_mark
E           AssertionError: ls <home>/.nvm/bin
1 failed, 279 deselected in 0.28s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k "read"
27 passed, 253 deselected in 8.47s
exit: 0

$ ./check.sh
252 files already formatted
2408 passed, 13 skipped in 112.35s (0:01:52)
✔ Validation passed
✔ Validation passed
exit: 0
