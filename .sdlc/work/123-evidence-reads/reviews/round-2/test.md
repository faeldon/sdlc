VERDICT: PASS

All four points kept from round 1 are fixed, and the tests prove each one.

- **`system(` in awk:** `AWK_RUNS_RE` is now `system\s*\(|@load|@include`. `NON_READS` has the `system (` row, and my tab-separated variant `system\t(` is also refused.
- **Digit redirect targets:** only `>&` with a digit target counts as a descriptor. `cat a >2`, `cat a > 1`, `echo hi >> 1`, `cat a 2>1`, `cat a &>1` and `cat a 1>2` all return False. `cat a 2>&1` and `cat a >&2` still return True. `NON_READS` has the rows for `>2`, `> 2`, `>> 1`, `2>1` and `&>1`.
- **`rg --pre`:** `rg` is refused when any argument starts with `--pre`, which covers `--pre-glob` and `--pre=`. `NON_READS` has three rows for it, and `rg -n x src` stays a read.
- **Run:** the full suite shows 2255 passed and 13 skipped.

## Notes
- **Command run:** `uv run --group dev pytest -q -n auto`. It collected tests, and none failed.
- **Spot checks of `is_read()`:** I ran extra cases by hand and all behaved correctly.
  - `cat a >| f` returns False.
  - `cat a >& f` returns False.
  - `cat a 2>/dev/null` returns True.
- **Not covered by `NON_READS` rows:** the tab variant of `system(`, `>|`, `>& f` and `1>2`. The code handles each correctly today, and they are minor gaps.
- **Coverage of R1–R3 and R6:** each has a test that fails without the change. These are the allowlist, the read that needs no `exit:`, the silent read that still owes one, and the builder report.
- **Reads that show output:** `test_a_read_showing_its_output_needs_no_exit` covers both a fenced and an unfenced read.
- **`checks.md`:** I did not read it this round, and nothing in the rework touches it.
