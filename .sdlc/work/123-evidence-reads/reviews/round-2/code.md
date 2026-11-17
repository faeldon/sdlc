VERDICT: PASS

All four kept changes from round 1 are done. I found no new problem in the reworked code.

## Notes

- **`_awk_reads`:** `AWK_RUNS_RE` is now `system\s*\(|@load|@include`. `awk 'BEGIN{system ("rm f")}'` and a tab-separated form both fail `is_read()`. `NON_READS` has the space-separated row.
- **Redirect branch:** a digit target passes only after `>&`. `cat a >2`, `cat a > 2`, `echo hi >> 1`, `cat a 2>1` and `cat a &>1` are all `NON_READS` rows and all fail. `cat a 2>&1` stays in `READS` and passes. I also checked `cat a >&2`, `cat a 1>&2` and `cat a 2>&1 | grep x`, which pass, and `cat a 1>2` and `cat a >| f`, which fail.
- **`rg`:** it is no longer in `READS` and is handled in `_simple_read`, which refuses any argument starting with `--pre`. That covers `--pre-glob` as well. The three `rg --pre` forms are `NON_READS` rows, and `rg -n x src` stays a read.
- **Done well:** every hole is a table row in `READS` or `NON_READS`, and one test runs both tables. The comments in the code give the reason for each rule.
- **Ran:** `uv run --group dev pytest -q -n auto tests/test_factory.py -k "read or evidence"` passed (32). I also ran an ad-hoc `is_read()` probe of the cases above. I did not run the full `./check.sh` gate.
- **Nit:** the redirect branch only handles `>&`, so `<&` (stdin duplication) is not in `REDIRECTS` and fails. That is strict in the safe direction and costs at most one mend, so no change is needed.
