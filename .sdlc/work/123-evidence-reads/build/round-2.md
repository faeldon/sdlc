All four kept changes from round 1 are fixed in `is_read()`, and the gate passes again with 2255 tests. The work is still uncommitted.

**Kept changes**
- **code C1 (awk `system`):** `system` is now matched by a regex that allows spaces before its `(`. So `awk 'BEGIN{system ("rm f")}'` is no longer a read.
- **code C2 (a digit after a redirect):** a digit after a redirect now passes only after `>&`, as in `2>&1` or `>&2`. After `>`, `>>` or `&>` the digit is a file name, so `cat a >2`, `cat a > 2`, `echo hi >> 1`, `cat a 2>1` and `cat a &>1` are now non-reads. C4 said a digit could also pass after `&>`. I didn't allow that: `&>1` writes a file named `1`, and the verifier's notes say the same.
- **code C3 (`rg --pre`):** I took `rg` off the plain-read list. It now has its own rule: any option starting with `--pre` (`--pre`, `--pre=…`, `--pre-glob`) makes it a non-read, because `--pre` runs a program on each file. `rg -n x src` is still a read.
- **test C4:** I added non-read rows for all the commands above, plus `rg --pre ./x y`, `rg --pre=./x y` and `rg --pre-glob '*.gz' --pre ./x y`. I added read rows for `cat a 2>&1` and `rg -n x src`. The table test failed on the new rows before the fixes and passes after them.

**`plan.md`:** the first file entry now notes where round 1 made the rules stricter than the spec's Design: the new `rg` rule, spaces before awk's `(`, and digits only after `>&`.

**`notes.md`:** no change; its two open items from round 1 are still there.

No decisions raised this round.

## Evidence

$ uv run --group dev pytest -q tests/test_factory.py -k changes_nothing   (new rows, before the fixes)
E       AssertionError: ['awk \'BEGIN{system ("rm f")}\'', 'cat a >2', 'cat a > 2', 'echo hi >> 1', 'cat a &>1', 'rg --pre ./x y', ...]
1 failed, 215 deselected in 0.23s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k changes_nothing   (after the fixes)
1 passed, 215 deselected in 0.20s
exit: 0

$ ./check.sh > /tmp/gate123.log 2>&1; echo "exit: $?"; grep -E "passed|failed|All checks|formatted|Validation" /tmp/gate123.log | grep -v warning
exit: 0
All checks passed!
257 files already formatted
2255 passed, 13 skipped in 113.49s (0:01:53)
✔ Validation passed
✔ Validation passed
exit: 0
